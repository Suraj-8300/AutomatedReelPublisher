"""
CDN Video Optimization and Compliance Engine for AutoReelStudio.
Prepares master video for flawless CDN streaming across Instagram Reels and YouTube Shorts.
Ensures faststart moov-first atom, strict 1080x1920 9:16 vertical format, and 48kHz audio.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30

class CDNOptimizer:
    """Prepares and validates videos for cloud CDN streaming and social platform ingestion."""

    @classmethod
    def probe_video(cls, video_path: Path) -> Dict[str, Any]:
        """Probes video technical specifications via ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(video_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not res.stdout:
            return {"valid": False, "error": "ffprobe failed"}

        try:
            data = json.loads(res.stdout)
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0.0))
            size = int(format_info.get("size", 0))

            v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
            a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)

            # Check moov atom position
            is_faststart = cls._check_faststart(video_path)

            return {
                "valid": True,
                "duration": duration,
                "size_mb": round(size / (1024 * 1024), 2),
                "faststart": is_faststart,
                "video": {
                    "codec": v_stream.get("codec_name") if v_stream else None,
                    "width": int(v_stream.get("width", 0)) if v_stream else 0,
                    "height": int(v_stream.get("height", 0)) if v_stream else 0,
                    "pix_fmt": v_stream.get("pix_fmt") if v_stream else None,
                },
                "audio": {
                    "codec": a_stream.get("codec_name") if a_stream else None,
                    "sample_rate": int(a_stream.get("sample_rate", 0)) if a_stream else 0,
                    "channels": int(a_stream.get("channels", 0)) if a_stream else 0,
                }
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def _check_faststart(video_path: Path) -> bool:
        """Inspects if 'moov' atom appears before 'mdat' in the MP4 container."""
        try:
            with open(video_path, "rb") as f:
                header = f.read(1024 * 128)
                moov_pos = header.find(b"moov")
                mdat_pos = header.find(b"mdat")
                if moov_pos != -1 and (mdat_pos == -1 or moov_pos < mdat_pos):
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def optimize_for_cdn(
        cls,
        input_video: Path,
        output_video: Optional[Path] = None
    ) -> Path:
        """
        Transcodes video to ensure faststart moov placement, 1080x1920 full screen,
        and 48kHz stereo AAC audio for instantaneous CDN playback.
        """
        input_video = Path(input_video).resolve()
        if output_video is None:
            output_video = input_video.parent / f"cdn_{input_video.name}"

        # FFmpeg transcode with faststart
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_video),
            "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264",
            "-preset", "fast",
            "-b:v", "4.5M",
            "-maxrate", "5.0M",
            "-bufsize", "8.0M",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-movflags", "+faststart",
            str(output_video)
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Generate thumbnail poster
        thumb_path = output_video.with_suffix(".jpg")
        thumb_cmd = [
            "ffmpeg", "-y",
            "-i", str(output_video),
            "-ss", "00:00:01.500",
            "-vframes", "1",
            str(thumb_path)
        ]
        subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return output_video

