#!/usr/bin/env python3
import os
import sys
import json
import random
import shutil
import time
import asyncio
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import OUTPUT_DIR, CACHE_DIR, VOICES
from core.creative_randomizer import GENRE_TAXONOMY, GENERATION_MODES
from core.genre_catalog import get_catalog_topics
from core.content_history import ContentHistory
from core.quality_control import QualityControlEngine
from core.cache_manager import CacheManager
from core.animal_storyteller import AnimalStoryteller, VISUAL_STYLES, ACTIVITIES, STORY_ARCHETYPES
from core.character_director import ANIMAL_SPECIES, UNUSUAL_DUOS
from generate import run_pipeline
from publishers.instagram.config import INBOX_DIR, ARCHIVE_DIR, INSTAGRAM_ACCOUNT_ID, META_ACCESS_TOKEN
from publishers.instagram.preprocessor import VideoPreprocessor
from publishers.instagram.metadata_linker import MetadataLinker
from publishers.instagram.queue_manager import ReelQueueManager
from publishers.instagram.publisher import MetaGraphPublisher as InstagramReelPublisher

PORT = int(os.environ.get("PORT", 8080))

class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that cleanly handles browser client disconnects without printing tracebacks."""
    def handle_error(self, request, client_address):
        exc_type, exc_val, _ = sys.exc_info()
        if exc_type in (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return # Silently ignore client disconnects
        if isinstance(exc_val, OSError) and exc_val.errno in (32, 104):
            return
        super().handle_error(request, client_address)

class ReelServerHandler(SimpleHTTPRequestHandler):
    """
    High-performance, CORS-enabled HTTP Request Handler for AutoReelStudio.
    Unified backend integrating ReelMakerAI generation and ReelPublisher Meta publishing.
    Serves static assets, video byte-range streams, and REST APIs.
    """

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass

    def finish(self):
        try:
            super().finish()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)

        # 1. Main UI
        if url.path in ["/", "/index.html"]:
            template_path = PROJECT_ROOT / "templates" / "index.html"
            if not template_path.exists():
                self.send_error(404, "Template index.html not found")
                return
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))

        # 2. Static Assets (CSS, JS, Images)
        elif url.path.startswith("/static/"):
            rel_path = url.path.replace("/static/", "")
            file_path = PROJECT_ROOT / "static" / rel_path
            if file_path.exists() and file_path.is_file():
                mime = "text/plain"
                if file_path.suffix == ".css":
                    mime = "text/css"
                elif file_path.suffix == ".js":
                    mime = "application/javascript"
                elif file_path.suffix in [".webp", ".png", ".jpg", ".jpeg"]:
                    mime = f"image/{file_path.suffix.replace('.', '')}"
                elif file_path.suffix == ".svg":
                    mime = "image/svg+xml"

                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.send_header("Cache-Control", "public, max-age=3600")
                self._set_cors_headers()
                self.end_headers()
                with open(file_path, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            else:
                self.send_error(404, "Static asset not found")

        # 3. Output Video Files (supports Byte-Range Streaming)
        elif url.path.startswith("/output/"):
            filename = Path(url.path).name
            file_path = OUTPUT_DIR / filename
            if file_path.exists() and file_path.suffix.lower() == ".mp4":
                self._serve_video_file(file_path)
            else:
                self.send_error(404, f"Video {filename} not found")

        # 4. Cache Files
        elif url.path.startswith("/cache/"):
            filename = Path(url.path).name
            file_path = CACHE_DIR / filename
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg" if file_path.suffix in [".jpg", ".jpeg"] else "application/octet-stream")
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self._set_cors_headers()
                self.end_headers()
                with open(file_path, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            else:
                self.send_error(404, "Cache asset not found")

        # 5. API: Meta Account Status & Quota
        elif url.path == "/api/status":
            status_data = self._get_account_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(status_data).encode("utf-8"))

        # 6. API: Genres Taxonomy
        elif url.path == "/api/genres":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(GENRE_TAXONOMY).encode("utf-8"))

        # 7. API: Dynamic Autonomous Topic Generator
        elif url.path == "/api/random-topic":
            genre = params.get("genre", [None])[0]
            if genre == "RANDOM":
                genre = None
            from core.idea_generator import IdeaGenerator
            duration = int(params.get("duration", ["15"])[0])
            candidates = IdeaGenerator.generate_idea_candidates(
                genre=genre,
                duration=duration,
                count=1
            )
            topic = candidates[0] if candidates else IdeaGenerator.generate_autonomous_idea(
                genre=genre or "science",
                duration=duration
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(topic).encode("utf-8"))

        # 8. API: Ranked autonomous idea candidates
        elif url.path == "/api/idea-bank":
            from core.idea_generator import IdeaGenerator
            genre = params.get("genre", [None])[0]
            if genre == "RANDOM":
                genre = None
            duration = int(params.get("duration", ["15"])[0])
            count = int(params.get("count", ["5"])[0])
            seed_value = params.get("seed", [None])[0]
            seed = int(seed_value) if seed_value else None
            ideas = IdeaGenerator.generate_idea_candidates(
                genre=genre, duration=duration, count=count, seed=seed
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "ideas": ideas}).encode("utf-8"))

        # 9. API: Content Generation History & Anti-Repetition Stats
        elif url.path == "/api/history":
            history = ContentHistory.get_recent_history(limit=25)
            dist = ContentHistory.get_genre_distribution(window_size=30)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"history": history, "distribution": dist}).encode("utf-8"))

        # 9. API: Gallery Archive & Publishing Receipts
        elif url.path == "/api/gallery":
            gallery_data = self._get_gallery_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(gallery_data).encode("utf-8"))

        # 10. API: Inspect Video Specs & QC
        elif url.path == "/api/inspect":
            video_name = params.get("video", [""])[0]
            res = self._inspect_video(video_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 11. API: Storage & Cache Stats
        elif url.path == "/api/cache-stats":
            stats = CacheManager.get_cache_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "stats": stats}).encode("utf-8"))

        # 11b. API: YouTube Channel Status & Auth URL
        elif url.path == "/api/youtube/status":
            try:
                from publishers.youtube.auth import YouTubeAuthenticator
                is_auth = YouTubeAuthenticator.is_authenticated()
                auth_url = ""
                if not is_auth:
                    try:
                        auth_url = YouTubeAuthenticator.get_or_start_auth_url()
                    except Exception as e:
                        auth_url = ""
                info = YouTubeAuthenticator.get_channel_info() if is_auth else {"authenticated": False}
                info["auth_url"] = auth_url
            except Exception as e:
                info = {"authenticated": False, "error": str(e), "auth_url": ""}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(info).encode("utf-8"))

        # 11c. API: 10-15 Creative Idea Queue Buffer
        elif url.path == "/api/queue":
            from idea_generation import IdeaQueueManager
            queue = IdeaQueueManager.get_queue()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "count": len(queue),
                "min_threshold": 10,
                "target_size": 15,
                "queue": queue
            }).encode("utf-8"))

        # 11d. API: 50 Reels/Day Quota Telemetry
        elif url.path == "/api/quota":
            from video_generation import QuotaGovernor
            status = QuotaGovernor.get_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "quota": status}).encode("utf-8"))

        # 11e. API: Ready Videos Publishing Queue (Paced 50 Reels/Day Distribution)
        elif url.path == "/api/publishing-queue":
            from publishers.dispatch_queue import PublishingQueueManager
            queue = PublishingQueueManager.get_queue()
            scheduled_count = len([i for i in queue if i.get("status") in ["scheduled", "pending"]])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "count": len(queue),
                "scheduled_count": scheduled_count,
                "queue": queue
            }).encode("utf-8"))

        # 12. API: Animal Storytelling Studio Options
        elif url.path == "/api/animal-options":
            species_list = [
                {"key": s["species"], "label": s["label"], "default_name": s["default_name"], "size": s.get("size", "small")}
                for s in ANIMAL_SPECIES
            ]
            styles_list = [
                {"key": k, "label": v["label"], "description": v["description"]}
                for k, v in VISUAL_STYLES.items()
            ]
            activities_list = [
                {"key": k, "label": v["label"]}
                for k, v in ACTIVITIES.items()
            ]
            genres_list = [
                {"key": k, "label": k.replace("_", " ").title(), "music_style": v["music_style"]}
                for k, v in STORY_ARCHETYPES.items()
            ]
            duos_list = [
                {
                    "duo_name": d["duo_name"],
                    "char1": d["char1"],
                    "char2": d["char2"]
                }
                for d in UNUSUAL_DUOS
            ]
            res = {
                "success": True,
                "species": species_list,
                "styles": styles_list,
                "activities": activities_list,
                "genres": genres_list,
                "duos": duos_list
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 13. API: Generate Random Animal Story Concept Preview
        elif url.path == "/api/random-animal-story":
            species = params.get("species", [None])[0]
            style = params.get("style", [None])[0]
            genre = params.get("genre", [None])[0]
            activity = params.get("activity", [None])[0]
            is_duo = params.get("is_duo", ["false"])[0].lower() in ["true", "1", "yes"]
            prompt = params.get("prompt", [None])[0]

            story = AnimalStoryteller.generate_story(
                animal_species=species if (species and species != "RANDOM") else None,
                visual_style=style if (style and style != "RANDOM") else None,
                story_genre=genre if (genre and genre != "RANDOM") else None,
                activity_type=activity if (activity and activity != "RANDOM") else None,
                is_duo=is_duo,
                custom_concept=prompt
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "story": story}).encode("utf-8"))

        else:
            self.send_error(404)

    def do_POST(self):
        url = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        # 1. API: Generate Draft Video Only
        if url.path == "/api/generate":
            res = self._handle_generate_draft(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 2. API: 1-Click Generate + Auto-Publish to Instagram
        elif url.path == "/api/generate-and-publish":
            res = self._handle_generate_and_publish(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 3. API: Publish an Existing Video File to Instagram
        elif url.path == "/api/publish-reel":
            res = self._handle_publish_reel(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 3b. API: Publish an Existing Video File to YouTube Shorts
        elif url.path == "/api/youtube/publish":
            try:
                from publishers.youtube.publisher import YouTubePublisher
                video_filename = data.get("video_filename", "")
                src_video = OUTPUT_DIR / Path(video_filename).name
                if not src_video.exists():
                    res = {"success": False, "error": f"Video file {video_filename} not found"}
                else:
                    title = data.get("title") or src_video.stem.replace("_", " ")
                    desc = data.get("description", "")
                    privacy = data.get("privacy", "public")
                    pub = YouTubePublisher()
                    res = pub.upload_short(src_video, title=title, description=desc, privacy_status=privacy)
            except Exception as e:
                res = {"success": False, "error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 3c. API: Replenish Idea Queue Buffer (10-15 Target)
        elif url.path == "/api/queue/replenish":
            from idea_generation import IdeaQueueManager
            res = IdeaQueueManager.replenish_if_needed()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 3d. API: 1-Click Upload Now (Bypass Scheduled Release Time)
        elif url.path == "/api/publishing-queue/upload-now":
            from publishers.dispatch_queue import PublishingQueueManager
            item_id = data.get("id")
            dry_run = data.get("dry_run", False)
            if item_id:
                res = PublishingQueueManager.publish_now(item_id, dry_run=dry_run)
            else:
                res = PublishingQueueManager.publish_next(dry_run=dry_run)
                if res is None:
                    res = {"success": False, "error": "No pending videos in publishing queue"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 3e. API: Cancel Scheduled Video in Publishing Queue
        elif url.path == "/api/publishing-queue/cancel":
            from publishers.dispatch_queue import PublishingQueueManager
            item_id = data.get("id", "")
            success = PublishingQueueManager.cancel_item(item_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": success}).encode("utf-8"))

        # 3f. API: Enqueue Video to Publishing Queue
        elif url.path == "/api/publishing-queue/enqueue":
            from publishers.dispatch_queue import PublishingQueueManager
            video_filename = data.get("video_filename", "")
            src_video = OUTPUT_DIR / Path(video_filename).name
            if not src_video.exists():
                res = {"success": False, "error": f"Video file {video_filename} not found"}
            else:
                platforms = data.get("platforms", ["instagram", "youtube"])
                title = data.get("title", src_video.stem.replace("_", " "))
                entry = PublishingQueueManager.enqueue(
                    video_path=src_video,
                    title=title,
                    platforms=platforms,
                    instagram_meta={"caption": data.get("caption", title)},
                    youtube_meta={"title": title, "description": data.get("description", ""), "tags": data.get("tags", [])}
                )
                res = {"success": True, "item": entry}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 4. API: Clear Cache Storage
        elif url.path == "/api/clear-cache":
            purged = CacheManager.purge_all()
            new_stats = CacheManager.get_cache_stats()
            res = {
                "success": True,
                "freed_mb": purged.get("freed_mb", 0.0),
                "deleted_count": purged.get("deleted_count", 0),
                "new_stats": new_stats
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        # 5. API: Delete Video from Archive
        elif url.path == "/api/delete-video":
            filename = data.get("filename")
            if not filename:
                res = {"success": False, "error": "No filename specified"}
            else:
                target = OUTPUT_DIR / Path(filename).name
                if target.exists() and target.suffix.lower() == ".mp4":
                    try:
                        target.unlink()
                        cap = INBOX_DIR / f"{target.stem}.txt"
                        if cap.exists():
                            cap.unlink(missing_ok=True)
                        res = {"success": True, "filename": filename}
                    except Exception as e:
                        res = {"success": False, "error": str(e)}
                else:
                    res = {"success": False, "error": "Video file not found"}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        else:
            self.send_error(404)

    def _serve_video_file(self, file_path: Path):
        try:
            file_size = file_path.stat().st_size
            range_header = self.headers.get("Range")

            if range_header:
                bytes_range = range_header.strip().replace("bytes=", "")
                start_str, end_str = bytes_range.split("-")
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                end = min(end, file_size - 1)
                chunk_len = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(chunk_len))
                self.send_header("Accept-Ranges", "bytes")
                self._set_cors_headers()
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(chunk_len))
                return

            # Full stream
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self._set_cors_headers()
            self.end_headers()

            with open(file_path, "rb") as f:
                while chunk := f.read(128 * 1024):
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass

    def _get_account_status(self):
        try:
            publisher = InstagramReelPublisher()
            acc = publisher.get_account_info()
            limit = publisher.get_publishing_limit()
            return {
                "success": True,
                "account": acc,
                "quota": limit
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "account": {"username": "sun_27417", "id": INSTAGRAM_ACCOUNT_ID}
            }

    def _get_gallery_data(self):
        video_files = sorted(OUTPUT_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
        published_receipts = {}
        for rec in ARCHIVE_DIR.glob("**/*.published.json"):
            try:
                with open(rec, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    base = d.get("original_file", "")
                    if base:
                        published_receipts[base] = d
            except Exception:
                pass

        gallery_data = []
        for vf in video_files:
            size_mb = f"{vf.stat().st_size / (1024 * 1024):.1f} MB"
            clean_name = vf.stem.replace("_", " ")[:40]
            receipt = published_receipts.get(vf.name, {})
            gallery_data.append({
                "name": clean_name,
                "filename": vf.name,
                "url": f"/output/{vf.name}",
                "size": size_mb,
                "published": bool(receipt),
                "permalink": receipt.get("instagram_permalink", "")
            })
        return gallery_data

    def _inspect_video(self, video_name: str):
        if not video_name:
            return {"success": False, "error": "No video specified"}
        target = OUTPUT_DIR / Path(video_name).name
        if not target.exists():
            return {"success": False, "error": f"File {video_name} not found"}

        try:
            probe = VideoPreprocessor.probe_video(target)
            comp = VideoPreprocessor.validate_compliance(probe)
            qc = QualityControlEngine.audit_video(target)
            return {
                "success": True,
                "probe": probe,
                "compliance": comp,
                "qc": qc
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_generate_draft(self, data: dict):
        prompt = data.get("prompt")
        duration = int(data.get("duration", 15))
        genre = data.get("genre")
        subgenre = data.get("subgenre")
        mode = data.get("mode", "balanced")
        caption_style = data.get("caption_style")
        voice = data.get("voice")
        if voice == "AUTO":
            voice = None
        music = data.get("music")
        if music == "AUTO":
            music = None
        theme = data.get("theme")
        seed = int(data.get("seed")) if data.get("seed") else None

        animal_species = data.get("animal_species")
        if animal_species == "RANDOM":
            animal_species = None
        visual_style = data.get("visual_style")
        if visual_style == "RANDOM":
            visual_style = None
        activity_type = data.get("activity_type")
        if activity_type == "RANDOM":
            activity_type = None
        is_duo = bool(data.get("is_duo", False))

        start = time.time()
        try:
            from video_generation import QuotaGovernor
            allowed, remaining, msg = QuotaGovernor.can_generate()
            if not allowed:
                return {"success": False, "error": msg}
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            video_file, storyboard, qc_result = loop.run_until_complete(run_pipeline(
                prompt=prompt,
                duration=duration,
                genre=genre,
                subgenre=subgenre,
                mode=mode,
                caption_style=caption_style,
                voice=voice,
                music_style=music,
                theme=theme,
                seed=seed,
                run_qc=True,
                animal_species=animal_species,
                visual_style=visual_style,
                activity_type=activity_type,
                is_duo=is_duo
            ))
            loop.close()
            elapsed = time.time() - start
            vf = Path(video_file)
            return {
                "success": True,
                "video_url": f"/output/{vf.name}",
                "filename": vf.name,
                "storyboard": storyboard,
                "qc": qc_result,
                "elapsed": elapsed
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_generate_and_publish(self, data: dict):
        prompt = data.get("prompt")
        duration = int(data.get("duration", 15))
        genre = data.get("genre")
        subgenre = data.get("subgenre")
        mode = data.get("mode", "balanced")
        caption_style = data.get("caption_style")
        voice = data.get("voice")
        if voice == "AUTO":
            voice = None
        music = data.get("music")
        if music == "AUTO":
            music = None
        theme = data.get("theme")
        seed = int(data.get("seed")) if data.get("seed") else None
        dry_run = data.get("dry_run", False)

        animal_species = data.get("animal_species")
        if animal_species == "RANDOM":
            animal_species = None
        visual_style = data.get("visual_style")
        if visual_style == "RANDOM":
            visual_style = None
        activity_type = data.get("activity_type")
        if activity_type == "RANDOM":
            activity_type = None
        is_duo = bool(data.get("is_duo", False))

        start = time.time()
        try:
            from video_generation import QuotaGovernor
            allowed, remaining, msg = QuotaGovernor.can_generate()
            if not allowed:
                return {"success": False, "error": msg}
            # 1. Synthesize Draft Video
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            video_file, storyboard, qc_result = loop.run_until_complete(run_pipeline(
                prompt=prompt,
                duration=duration,
                genre=genre,
                subgenre=subgenre,
                mode=mode,
                caption_style=caption_style,
                voice=voice,
                music_style=music,
                theme=theme,
                seed=seed,
                run_qc=True,
                animal_species=animal_species,
                visual_style=visual_style,
                activity_type=activity_type,
                is_duo=is_duo
            ))
            loop.close()

            src_path = Path(video_file)

            # 2. Queue into Instagram Inbox & Publish
            target = INBOX_DIR / src_path.name
            shutil.copy(str(src_path), str(target))

            # Companion metadata
            caption = MetadataLinker.generate_caption(
                title=storyboard.get("title", src_path.stem),
                genre=storyboard.get("genre", "science"),
                hook=storyboard.get("hook"),
                source=storyboard.get("source")
            )
            caption_file = INBOX_DIR / f"{src_path.stem}.txt"
            with open(caption_file, "w", encoding="utf-8") as f:
                f.write(caption)

            manager = ReelQueueManager()
            result = manager.process_video_file(target, dry_run=dry_run)
            elapsed = time.time() - start

            # Optional YouTube Shorts Publishing
            destinations = data.get("destinations", ["instagram"])
            if isinstance(destinations, str):
                destinations = [destinations]

            yt_receipt = None
            if "youtube" in destinations or "both" in destinations:
                try:
                    from publishers.youtube.auth import YouTubeAuthenticator
                    from publishers.youtube.publisher import YouTubePublisher
                    if YouTubeAuthenticator.is_authenticated():
                        pub = YouTubePublisher()
                        yt_receipt = pub.upload_short(
                            src_path,
                            title=storyboard.get("title", src_path.stem),
                            description=storyboard.get("script", ""),
                            privacy_status="public" if not dry_run else "private"
                        )
                    else:
                        yt_receipt = {"success": False, "error": "YouTube not authenticated"}
                except Exception as ex:
                    yt_receipt = {"success": False, "error": str(ex)}

            if result.get("success"):
                receipt = result.get("receipt", {})
                return {
                    "success": True,
                    "video_url": f"/output/{src_path.name}",
                    "filename": src_path.name,
                    "storyboard": storyboard,
                    "qc": qc_result,
                    "permalink": receipt.get("instagram_permalink"),
                    "media_id": receipt.get("instagram_media_id"),
                    "youtube": yt_receipt,
                    "elapsed": elapsed
                }
            else:
                return {
                    "success": False,
                    "video_url": f"/output/{src_path.name}",
                    "filename": src_path.name,
                    "storyboard": storyboard,
                    "qc": qc_result,
                    "error": result.get("error", "Instagram publish failed"),
                    "elapsed": elapsed
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_publish_reel(self, data: dict):
        video_filename = data.get("video_filename", "")
        dry_run = data.get("dry_run", False)
        src_video = OUTPUT_DIR / Path(video_filename).name

        if not src_video.exists():
            return {"success": False, "error": f"Video file not found: {video_filename}"}

        try:
            target = INBOX_DIR / src_video.name
            shutil.copy(str(src_video), str(target))

            caption = MetadataLinker.generate_caption_from_title(src_video.stem)
            caption_file = INBOX_DIR / f"{src_video.stem}.txt"
            with open(caption_file, "w", encoding="utf-8") as f:
                f.write(caption)

            manager = ReelQueueManager()
            result = manager.process_video_file(target, dry_run=dry_run)

            if result.get("success"):
                receipt = result.get("receipt", {})
                return {
                    "success": True,
                    "permalink": receipt.get("instagram_permalink"),
                    "media_id": receipt.get("instagram_media_id")
                }
            else:
                return {"success": False, "error": result.get("error", "Publish failed")}
        except Exception as e:
            return {"success": False, "error": str(e)}

def start_scheduler_thread():
    """Background daemon thread to automatically release scheduled videos when their release time arrives."""
    import threading
    def _worker():
        from publishers.dispatch_queue import PublishingQueueManager
        while True:
            try:
                PublishingQueueManager.process_due_items()
            except Exception as e:
                print(f"⚠️ Scheduler ticker error: {e}")
            time.sleep(30)
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def start_server(port=PORT):
    # Auto-prune cache on launch
    prune_res = CacheManager.auto_prune()
    stats = CacheManager.get_cache_stats()

    # Start background scheduled publishing dispatcher
    start_scheduler_thread()

    server = QuietThreadingHTTPServer(("0.0.0.0", port), ReelServerHandler)
    print("=" * 65)
    print(f"🚀 AUTOREELSTUDIO RUNNING AT: http://localhost:{port}")
    print(f"🎬 Subsystems:         ReelMakerAI (Generator) + ReelPublisher (Meta Reels API)")
    print(f"📱 Instagram Account:  @{os.environ.get('INSTAGRAM_USERNAME', 'sun_27417')}")
    print(f"📦 Active Ingestion Bridge: Meta Native Direct Resumable Upload (100% Free, Zero Tunnels)")
    print(f"💾 Storage Cache:      {stats['total_mb']} MB ({stats['file_count']} files, auto-pruned {prune_res['freed_mb']} MB)")
    print("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    start_server()
