#!/usr/bin/env python3
"""
AutoReelStudio — Modern Web Studio Server.
Provides REST APIs for video generation, file upload, ready/published media inspection,
video byte-range streaming, and direct publishing to Instagram and YouTube.
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
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from video.config import OUTPUT_DIR, PUBLISHED_DIR, CACHE_DIR
from video.generator import ReelGenerator
from autoreel import publish_direct
from instagram.publisher import MetaGraphPublisher
from youtube.auth import YouTubeAuthenticator

PORT = int(os.environ.get("PORT", 8080))

# Shared state for background video generation
generation_state = {
    "is_generating": False,
    "current_topic": "",
    "current_pillar": "",
    "progress": 0,
    "status_message": "Idle",
    "last_result": None,
    "error": None
}
state_lock = threading.Lock()


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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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
        elif path == "/api/generate/status":
            self.handle_api_generate_status()
        elif path.startswith("/media/output/"):
            filename = urllib.parse.unquote(path.replace("/media/output/", ""))
            self.serve_video_file(OUTPUT_DIR / filename)
        elif path.startswith("/media/published/"):
            filename = urllib.parse.unquote(path.replace("/media/published/", ""))
            self.serve_video_file(PUBLISHED_DIR / filename)
        elif path.startswith("/static/"):
            # Serve static files from static directory
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

        if path == "/api/generate":
            self.handle_api_generate(body)
        elif path == "/api/publish":
            self.handle_api_publish(body)
        elif path == "/api/upload":
            self.handle_api_upload(body)
        else:
            self.send_error(404, "Unknown API endpoint")

    # ── Handlers ──────────────────────────────────────────────────────────

    def serve_app(self):
        """Serves the single-page React studio app."""
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

    def serve_video_file(self, file_path: Path):
        """Serves video file with HTTP 206 Partial Content support for scrubbing."""
        file_path = file_path.resolve()
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "Video file not found")
            return

        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header:
            # Parse Range: bytes=start-end
            try:
                ranges = range_header.replace("bytes=", "").split("-")
                start = int(ranges[0])
                end = int(ranges[1]) if ranges[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", "video/mp4")
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

        # Full file fallback
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

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
        """Returns the list of ready videos in output/."""
        videos = []
        for p in sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True):
            stat = p.stat()
            videos.append({
                "filename": p.name,
                "title": p.stem.replace("_", " ").title(),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "stream_url": f"/media/output/{urllib.parse.quote(p.name)}"
            })
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

        # Add stream URLs
        for r in recorded:
            r["stream_url"] = f"/media/published/{urllib.parse.quote(r.get('filename', ''))}"

        self.send_json({"published": recorded})

    def handle_api_generate_status(self):
        with state_lock:
            self.send_json(generation_state)

    def handle_api_generate(self, body: bytes):
        """Triggers asynchronous reel generation."""
        try:
            req = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            req = {}

        pillar = req.get("pillar", "animal_story")
        prompt = req.get("prompt", "auto")
        voice = req.get("voice")
        music = req.get("music")
        visuals = req.get("visuals", "auto")

        with state_lock:
            if generation_state["is_generating"]:
                self.send_json({"error": "Generation already in progress"}, status=409)
                return
            generation_state["is_generating"] = True
            generation_state["current_topic"] = prompt
            generation_state["current_pillar"] = pillar
            generation_state["status_message"] = "Starting generation..."
            generation_state["progress"] = 10
            generation_state["error"] = None

        def worker():
            try:
                with state_lock:
                    generation_state["status_message"] = "Writing viral script & sourcing visuals..."
                    generation_state["progress"] = 35

                mp4_path, meta = ReelGenerator.generate(
                    topic=prompt,
                    pillar=pillar if pillar != "auto" else None,
                    voice_override=voice,
                    music_override=music,
                    visuals_override=visuals
                )

                with state_lock:
                    generation_state["is_generating"] = False
                    generation_state["progress"] = 100
                    generation_state["status_message"] = "Completed successfully!"
                    generation_state["last_result"] = {
                        "filename": mp4_path.name,
                        "topic": meta.get("topic"),
                        "duration": meta.get("duration")
                    }

            except Exception as e:
                with state_lock:
                    generation_state["is_generating"] = False
                    generation_state["error"] = str(e)
                    generation_state["status_message"] = f"Failed: {e}"

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        self.send_json({"status": "started", "topic": prompt, "pillar": pillar})

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

        platforms = req.get("platforms", ["all"])
        title = req.get("title", filename.replace("_", " "))
        caption = req.get("caption", title)
        dry_run = bool(req.get("dry_run", False))

        vpath = OUTPUT_DIR / filename
        if not vpath.exists():
            # Check if it was already published
            if (PUBLISHED_DIR / filename).exists():
                vpath = PUBLISHED_DIR / filename
            else:
                self.send_json({"error": f"File '{filename}' not found in output/"}, status=404)
                return

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

    def handle_api_upload(self, body: bytes):
        """Accepts uploaded video file and writes it to output/."""
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" in content_type:
            # Parse multipart boundary
            boundary = content_type.split("boundary=")[1].encode()
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
                                filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in raw_fn)
                    file_data = part[header_end + 4:].rstrip(b"\r\n")
                    break

            if file_data:
                dest = OUTPUT_DIR / filename
                with open(dest, "wb") as f:
                    f.write(file_data)
                self.send_json({"success": True, "filename": filename, "path": f"/media/output/{filename}"})
                return

        self.send_json({"error": "Invalid upload payload"}, status=400)

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
    run_server()
