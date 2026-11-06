"""
AI Video Generation Engine (Google Veo & Pollinations Video) for AutoReelStudio.

Supports:
1. Google Veo via google-genai Python SDK (when model/preview enabled on Gemini key).
2. Pollinations Video API (gen.pollinations.ai/video/) when key configured.
3. Automated fallback to cinematic camera motion and HD B-Roll.
4. Exporting camera-ready prompt specs for external video generators (Kling, Luma, Runway, Sora).
"""

import os
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List

from video.config import (
    CACHE_DIR, GEMINI_API_KEY, TARGET_WIDTH, TARGET_HEIGHT
)

_VEO_CACHE = CACHE_DIR / "veo_videos"
_VEO_CACHE.mkdir(parents=True, exist_ok=True)


class VeoVideoEngine:
    """
    Direct interface for AI-generated moving video clips.
    """

    @classmethod
    def is_veo_available(cls) -> bool:
        """Checks if Google Veo is accessible via the current GEMINI_API_KEY."""
        if not GEMINI_API_KEY:
            return False
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            models = [m.name for m in client.models.list()]
            return any("veo" in m.lower() for m in models)
        except Exception:
            return False

    @classmethod
    def generate_veo_clip(
        cls,
        prompt: str,
        duration_sec: float = 5.0,
        output_path: Optional[Path] = None,
        aspect_ratio: str = "9:16",
    ) -> Optional[Path]:
        """
        Attempts to generate a real AI video clip using Google Veo.
        Returns the path to the downloaded MP4 file, or None if Veo is not available.
        """
        if not GEMINI_API_KEY:
            return None

        out_file = output_path or (_VEO_CACHE / f"veo_{abs(hash(prompt)) % 10000000}.mp4")
        if out_file.exists() and out_file.stat().st_size > 50000:
            return out_file

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=GEMINI_API_KEY)
            print(f"🎬 Submitting prompt to Google Veo: '{prompt[:60]}...'")

            operation = client.models.generate_videos(
                model="veo-3.1-fast-generate-preview",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    negative_prompt="blurry, distorted, low quality, cartoon, watermark",
                    aspect_ratio=aspect_ratio,
                    resolution="720p",
                ),
            )

            print("⏳ Polling Veo video generation job...")
            max_wait = 180
            elapsed = 0
            while not operation.done and elapsed < max_wait:
                time.sleep(10)
                elapsed += 10
                operation = client.operations.get(operation)

            if operation.done and hasattr(operation, "response") and operation.response.generated_videos:
                gen_video = operation.response.generated_videos[0]
                gen_video.video.save(str(out_file))
                print(f"✅ Downloaded Veo video clip: {out_file.name}")
                return out_file

        except Exception as e:
            print(f"⚠️ Veo generation not active on this tier ({e})")

        return None

    @classmethod
    def generate_pollinations_video(
        cls,
        prompt: str,
        api_key: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Attempts generation via Pollinations Video API if an API key is available.
        """
        key = api_key or os.getenv("POLLINATIONS_API_KEY")
        if not key:
            return None

        out_file = output_path or (_VEO_CACHE / f"pollin_vid_{abs(hash(prompt)) % 10000000}.mp4")
        if out_file.exists() and out_file.stat().st_size > 50000:
            return out_file

        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://gen.pollinations.ai/video/{encoded_prompt}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": "AutoReelStudio/2.0"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(out_file, "wb") as f:
                f.write(resp.read())
            if out_file.exists() and out_file.stat().st_size > 20000:
                print(f"✅ Generated Pollinations AI video: {out_file.name}")
                return out_file
        except Exception as e:
            print(f"⚠️ Pollinations video request failed: {e}")

        return None
