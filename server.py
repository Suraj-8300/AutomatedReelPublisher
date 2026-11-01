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
from core.idea_generator import generate_random_topic, get_topics_by_niche
from generate import run_pipeline
from instagram_pipeline.config import INBOX_DIR, ARCHIVE_DIR, INSTAGRAM_ACCOUNT_ID, META_ACCESS_TOKEN
from instagram_pipeline.preprocessor import VideoPreprocessor
from instagram_pipeline.metadata_linker import MetadataLinker
from instagram_pipeline.queue_manager import ReelQueueManager
from instagram_pipeline.publisher import MetaGraphPublisher as InstagramReelPublisher

PORT = int(os.environ.get("PORT", 8080))

class ReelServerHandler(SimpleHTTPRequestHandler):
    """
    High-performance, CORS-enabled HTTP Request Handler for ReelPublisher Studio.
    Serves static assets, video byte-range streams, and REST APIs.
    """

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

        # 6. API: Random Topic Generator
        elif url.path == "/api/random-topic":
            niche = params.get("niche", ["RANDOM"])[0]
            if niche != "RANDOM":
                topics = get_topics_by_niche(niche)
                topic = random.choice(topics).copy() if topics else generate_random_topic()
            else:
                topic = generate_random_topic()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(topic).encode("utf-8"))

        # 7. API: Gallery Archive & Publishing Receipts
        elif url.path == "/api/gallery":
            gallery_data = self._get_gallery_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(gallery_data).encode("utf-8"))

        # 8. API: Inspect Video Specs
        elif url.path == "/api/inspect":
            video_name = params.get("video", [""])[0]
            res = self._inspect_video(video_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

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

        else:
            self.send_error(404)

    def _serve_video_file(self, file_path: Path):
        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header:
            # Parse Range: bytes=start-end
            try:
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
            except Exception:
                pass

        # Full stream
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self._set_cors_headers()
        self.end_headers()

        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(128 * 1024):
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
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
        # Scan archive for published receipts
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
            return {
                "success": True,
                "probe": probe,
                "compliance": comp
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_generate_draft(self, data: dict):
        prompt = data.get("prompt")
        duration = int(data.get("duration", 15))
        voice = data.get("voice", "en-US-ChristopherNeural")
        music = data.get("music", "cyber_pulse")
        theme = data.get("theme", None)

        start = time.time()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            video_file = loop.run_until_complete(run_pipeline(
                prompt=prompt,
                duration=duration,
                voice=voice,
                music_style=music,
                theme=theme
            ))
            loop.close()
            elapsed = time.time() - start
            vf = Path(video_file)
            return {
                "success": True,
                "video_url": f"/output/{vf.name}",
                "filename": vf.name,
                "elapsed": elapsed
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_generate_and_publish(self, data: dict):
        prompt = data.get("prompt")
        duration = int(data.get("duration", 15))
        voice = data.get("voice", "en-US-ChristopherNeural")
        music = data.get("music", "cyber_pulse")
        theme = data.get("theme", None)
        dry_run = data.get("dry_run", False)

        start = time.time()
        try:
            # 1. Synthesize Draft Video
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            video_file = loop.run_until_complete(run_pipeline(
                prompt=prompt,
                duration=duration,
                voice=voice,
                music_style=music,
                theme=theme
            ))
            loop.close()

            src_path = Path(video_file)

            # 2. Queue into Instagram Inbox & Publish
            target = INBOX_DIR / src_path.name
            shutil.copy(str(src_path), str(target))

            # Companion metadata
            caption = MetadataLinker.generate_caption_from_title(src_path.stem)
            caption_file = INBOX_DIR / f"{src_path.stem}.txt"
            with open(caption_file, "w", encoding="utf-8") as f:
                f.write(caption)

            manager = ReelQueueManager()
            result = manager.process_video_file(target, dry_run=dry_run)
            elapsed = time.time() - start

            if result.get("success"):
                receipt = result.get("receipt", {})
                return {
                    "success": True,
                    "video_url": f"/output/{src_path.name}",
                    "filename": src_path.name,
                    "permalink": receipt.get("instagram_permalink"),
                    "media_id": receipt.get("instagram_media_id"),
                    "elapsed": elapsed
                }
            else:
                return {
                    "success": False,
                    "video_url": f"/output/{src_path.name}",
                    "filename": src_path.name,
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

def start_server(port=PORT):
    server = ThreadingHTTPServer(("0.0.0.0", port), ReelServerHandler)
    print("=" * 60)
    print(f"🚀 REEL PUBLISHER STUDIO RUNNING AT: http://localhost:{port}")
    print(f"📱 Instagram Account:  @{os.environ.get('INSTAGRAM_USERNAME', 'sun_27417')}")
    print(f"📦 Active Cloud Bridge: Zero-Card OpenSSH TLS Tunnel (*.lhr.life)")
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    start_server()
