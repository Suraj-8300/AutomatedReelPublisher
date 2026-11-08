#!/usr/bin/env python3
"""
AutoReelStudio — Modern Video Upload, AI Understanding & Publishing Studio Server.
Provides REST APIs for:
- Video file upload and streaming
- Native Gemini Multimodal Video Reading & AI Caption Generation
- Metadata editing (Title, Hook, Instagram Caption, Hashtags, YouTube Description)
- 1-Click Publishing to Instagram Reels & YouTube Shorts
- Published archive inspection & live permalink tracking
"""

import os
import sys
import json
import time
import shutil
import urllib.parse
import threading
import mimetypes
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from video.config import OUTPUT_DIR, PUBLISHED_DIR, CACHE_DIR
from video.video_analyzer import VideoAnalyzer
from video.cdn_optimizer import CDNOptimizer
from autoreel import publish_direct
from instagram.publisher import MetaGraphPublisher
from youtube.auth import YouTubeAuthenticator

PORT = int(os.environ.get("PORT", 8080))


class ReelStudioHandler(SimpleHTTPRequestHandler):
    """CORS-enabled, byte-range streaming, REST API handler for AutoReelStudio."""

    def log_message(self, format, *args):
        # Keep terminal output clean
        if "/api/" in args[0] or "/media/" in args[0]:
            pass
        else:
            super().log_message(format, *args)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/" or path == "/index.html":
            self.serve_app()
        elif path == "/api/status":
            self.handle_api_status()
        elif path == "/api/videos/ready":
            self.handle_api_ready_videos()
        elif path == "/api/videos/published":
            self.handle_api_published_videos()
        elif path.startswith("/media/output/"):
            filename = urllib.parse.unquote(path.replace("/media/output/", ""))
            self.serve_media_file(OUTPUT_DIR / filename)
        elif path.startswith("/media/published/"):
            filename = urllib.parse.unquote(path.replace("/media/published/", ""))
            self.serve_media_file(PUBLISHED_DIR / filename)
        elif path.startswith("/static/"):
            local_path = PROJECT_ROOT / path.lstrip("/")
            if local_path.exists() and local_path.is_file():
                self.serve_static_file(local_path)
            else:
                self.send_error(404, "Static file not found")
        else:
            self.serve_app()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if path == "/api/upload":
            self.handle_api_upload(body)
        elif path == "/api/video/analyze":
            self.handle_api_video_analyze(body)
        elif path == "/api/video/update-metadata":
            self.handle_api_video_update(body)
        elif path == "/api/video/delete":
            self.handle_api_video_delete(body)
        elif path == "/api/publish":
            self.handle_api_publish(body)
        elif path == "/api/publish-all":
            self.handle_api_publish_all()
        else:
            self.send_error(404, "Unknown API endpoint")

    # ── Media & App Serving ───────────────────────────────────────────────

    def serve_app(self):
        """Serves the single-page studio web app."""
        index_file = PROJECT_ROOT / "templates" / "index.html"
        if not index_file.exists():
            self.send_error(404, "Template index.html not found")
            return

        with open(index_file, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_static_file(self, file_path: Path):
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_media_file(self, file_path: Path):
        """Serves video files with HTTP 206 partial content support or images directly."""
        file_path = file_path.resolve()
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File not found")
            return

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        file_size = file_path.stat().st_size

        # Image files (e.g. thumbnails)
        if content_type.startswith("image/"):
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(data)
            return

        # Video files with byte-range scrubbing
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            try:
                byte_range = range_header.replace("bytes=", "").split("-")
                start = int(byte_range[0])
                end = int(byte_range[1]) if byte_range[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_remaining = length
                    while bytes_remaining > 0:
                        chunk_size = min(bytes_remaining, 64 * 1024)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        bytes_remaining -= len(chunk)
                return
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception:
                pass

        # Full video fallback
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    # ── Status & Listing Handlers ─────────────────────────────────────────

    def handle_api_status(self):
        """Audits live Instagram and YouTube credentials and folder counts."""
        # 1. Instagram status
        ig_info = {"configured": False, "username": "", "id": "", "quota_usage": 0, "quota_total": 100}
        try:
            pub = MetaGraphPublisher()
            if pub.is_configured():
                ig_info["configured"] = True
                acc = pub.get_account_info()
                ig_info["username"] = acc.get("username", "@sun_27417")
                ig_info["id"] = acc.get("id", pub.account_id)
                lim = pub.get_publishing_limit()
                ig_info["quota_usage"] = lim.get("quota_usage", 0)
                ig_info["quota_total"] = lim.get("quota_total", 100)
        except Exception as e:
            ig_info["error"] = str(e)

        # 2. YouTube status
        yt_info = {"authenticated": False, "channel_title": "", "channel_id": "", "subscribers": "0"}
        try:
            service = YouTubeAuthenticator.get_authenticated_service()
            if service:
                yt_info["authenticated"] = True
                resp = service.channels().list(mine=True, part="snippet,statistics").execute()
                items = resp.get("items", [])
                if items:
                    ch = items[0]
                    yt_info["channel_title"] = ch.get("snippet", {}).get("title", "Unknown")
                    yt_info["channel_id"] = ch.get("id", "Unknown")
                    yt_info["subscribers"] = ch.get("statistics", {}).get("subscriberCount", "0")
        except Exception as e:
            yt_info["error"] = str(e)

        ready_count = len(list(OUTPUT_DIR.glob("*.mp4")))
        published_count = len(list(PUBLISHED_DIR.glob("*.mp4")))

        data = {
            "instagram": ig_info,
            "youtube": yt_info,
            "counts": {
                "ready": ready_count,
                "published": published_count
            }
        }
        self.send_json(data)

    def handle_api_ready_videos(self):
        """Returns the list of ready videos in output/ enriched with AI companion metadata."""
        videos = []
        for p in sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True):
            meta = VideoAnalyzer.get_video_metadata(p)
            videos.append(meta)
        self.send_json({"videos": videos})

    def handle_api_published_videos(self):
        """Returns the list of published videos with YouTube and Instagram URLs."""
        history_file = PROJECT_ROOT / "data" / "published_history.json"
        recorded = []
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    recorded = json.load(f)
            except Exception:
                recorded = []

        # Merge with any files in published/ that might not be in history
        known_files = {r.get("filename") for r in recorded}
        for p in sorted(PUBLISHED_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True):
            if p.name not in known_files:
                stat = p.stat()
                recorded.append({
                    "filename": p.name,
                    "title": p.stem.replace("_", " ").title(),
                    "caption": p.stem.replace("_", " "),
                    "published_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)),
                    "youtube_url": None,
                    "instagram_id": None,
                    "instagram_url": None,
                })

        # Filter to only existing files in published/
        valid_recorded = []
        for r in recorded:
            fn = r.get("filename", "")
            if not (PUBLISHED_DIR / fn).exists():
                continue
            r["stream_url"] = f"/media/published/{urllib.parse.quote(fn)}"
            thumb = PUBLISHED_DIR / f"{Path(fn).stem}_thumb.jpg"
            if thumb.exists():
                r["thumbnail"] = f"/media/published/{urllib.parse.quote(thumb.name)}"
            else:
                r["thumbnail"] = None
            valid_recorded.append(r)

        self.send_json({"published": valid_recorded})

    # ── Video Upload & AI Understanding Handlers ──────────────────────────

    def handle_api_upload(self, body: bytes):
        """Accepts uploaded video, saves to output/, and runs AI video understanding."""
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_json({"error": "Content-Type must be multipart/form-data"}, status=400)
            return

        boundary = content_type.split("boundary=")[1].strip().encode()
        parts = body.split(b"--" + boundary)
        file_data = None
        filename = f"uploaded_reel_{int(time.time())}.mp4"

        for part in parts:
            if b'filename="' in part:
                header_end = part.find(b"\r\n\r\n")
                headers = part[:header_end].decode("utf-8", errors="ignore")
                for line in headers.splitlines():
                    if "filename=" in line:
                        raw_fn = line.split('filename="')[1].split('"')[0]
                        if raw_fn:
                            clean_stem = "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(raw_fn).stem)
                            filename = f"{clean_stem}_{int(time.time())}.mp4"
                file_data = part[header_end + 4:].rstrip(b"\r\n")
                break

        if not file_data:
            self.send_json({"error": "No video data found in multipart payload"}, status=400)
            return

        dest = OUTPUT_DIR / filename
        with open(dest, "wb") as f:
            f.write(file_data)

        # Optimize for streaming if not faststart
        try:
            CDNOptimizer.ensure_faststart(dest)
        except Exception:
            pass

        # Trigger AI Reading & Analysis
        try:
            metadata = VideoAnalyzer.analyze_video(dest)
            self.send_json({
                "success": True,
                "filename": filename,
                "metadata": metadata,
                "path": f"/media/output/{filename}"
            })
        except Exception as e:
            self.send_json({
                "success": True,
                "filename": filename,
                "warning": f"Uploaded successfully, but analysis notice: {e}",
                "metadata": VideoAnalyzer.get_video_metadata(dest),
                "path": f"/media/output/{filename}"
            })

    def handle_api_video_analyze(self, body: bytes):
        """Re-analyzes an existing video with optional custom instructions."""
        try:
            req = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req = {}

        filename = req.get("filename")
        instruction = req.get("instruction")

        if not filename:
            self.send_json({"error": "filename is required"}, status=400)
            return

        vpath = OUTPUT_DIR / filename
        if not vpath.exists():
            vpath = PUBLISHED_DIR / filename
        if not vpath.exists():
            self.send_json({"error": f"File '{filename}' not found"}, status=404)
            return

        try:
            metadata = VideoAnalyzer.analyze_video(vpath, custom_instruction=instruction)
            self.send_json({"success": True, "metadata": metadata})
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def handle_api_video_update(self, body: bytes):
        """Updates edited title, caption, hashtags, or description in companion json."""
        try:
            req = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req = {}

        filename = req.get("filename")
        if not filename:
            self.send_json({"error": "filename is required"}, status=400)
            return

        vpath = OUTPUT_DIR / filename
        if not vpath.exists():
            vpath = PUBLISHED_DIR / filename
        if not vpath.exists():
            self.send_json({"error": f"File '{filename}' not found"}, status=404)
            return

        meta = VideoAnalyzer.get_video_metadata(vpath)

        # Update fields if provided
        for field in ["title", "hook", "summary", "instagram_caption", "youtube_title", "youtube_description", "hashtags"]:
            if field in req:
                meta[field] = req[field]

        companion_json = vpath.parent / f"{vpath.stem}.json"
        with open(companion_json, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        self.send_json({"success": True, "metadata": meta})

    def handle_api_video_delete(self, body: bytes):
        """Deletes a video from output/."""
        try:
            req = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req = {}

        filename = req.get("filename")
        if not filename:
            self.send_json({"error": "filename is required"}, status=400)
            return

        vpath = OUTPUT_DIR / filename
        if not vpath.exists():
            self.send_json({"error": f"File '{filename}' not found in output/"}, status=404)
            return

        # Delete video, companion json, and thumbnail
        vpath.unlink(missing_ok=True)
        (OUTPUT_DIR / f"{vpath.stem}.json").unlink(missing_ok=True)
        (OUTPUT_DIR / f"{vpath.stem}_thumb.jpg").unlink(missing_ok=True)

        self.send_json({"success": True, "message": f"Deleted {filename}"})

    # ── Publishing Handlers ───────────────────────────────────────────────

    def handle_api_publish(self, body: bytes):
        """Directly publishes an MP4 from output/ and moves it to published/."""
        try:
            req = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req = {}

        filename = req.get("filename")
        if not filename:
            self.send_json({"error": "filename is required"}, status=400)
            return

        vpath = OUTPUT_DIR / filename
        if not vpath.exists():
            if (PUBLISHED_DIR / filename).exists():
                vpath = PUBLISHED_DIR / filename
            else:
                self.send_json({"error": f"File '{filename}' not found in output/"}, status=404)
                return

        # Read companion metadata if available
        meta = VideoAnalyzer.get_video_metadata(vpath)

        platforms = req.get("platforms", ["all"])
        title = req.get("title") or meta.get("title") or filename.replace("_", " ")
        caption = req.get("caption") or meta.get("instagram_caption") or title
        dry_run = bool(req.get("dry_run", False))

        try:
            dest_path = publish_direct(
                video_path=vpath,
                platforms=platforms,
                title=title,
                caption=caption,
                dry_run=dry_run
            )
            self.send_json({
                "success": True,
                "message": f"Successfully published {filename}",
                "dest_path": str(dest_path.name),
                "is_dry_run": dry_run
            })
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def handle_api_publish_all(self):
        """Batch publishes all ready videos in output/."""
        from scripts.publish_all_output import run_publish_all
        try:
            run_publish_all()
            self.send_json({"success": True, "message": "All ready videos published successfully!"})
        except Exception as e:
            self.send_json({"error": str(e)}, status=500)

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = PORT):
    server = ThreadingHTTPServer(("0.0.0.0", port), ReelStudioHandler)
    print("\n" + "=" * 65)
    print(f"🚀 AutoReelStudio Web UI Server running at: http://localhost:{port}")
    print(f"📁 Output folder:    {OUTPUT_DIR}")
    print(f"📁 Published folder: {PUBLISHED_DIR}")
    print("=" * 65 + "\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AutoReelStudio server...")
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AutoReelStudio Web UI Server")
    parser.add_argument("--port", type=int, default=PORT, help=f"Server port (default: {PORT})")
    args = parser.parse_args()
    run_server(args.port)
