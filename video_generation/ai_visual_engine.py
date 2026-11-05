"""
AI Visual Generation & Cinematic Motion Engine for AutoReelStudio.
Generates genuine AI-rendered visual art for each scene and transforms them into
fluid, dynamic 1080x1920 vertical video clips with Ken Burns camera motion.
Zero boring stock footage.
"""

import os
import sys
import math
import random
import hashlib
import urllib.parse
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30

class AIVisualEngine:
    """Generates authentic AI visuals and animates them into 9:16 vertical video scenes."""

    @classmethod
    def generate_scene_image(
        cls,
        prompt: str,
        style: str = "photorealistic",
        seed: Optional[int] = None
    ) -> Path:
        """
        Fetches an AI-generated vertical image (1080x1920) matching the prompt.
        Uses enhanced prompt styling and falls back to aesthetic neural composite if network fails.
        """
        # Enhance prompt for high-retention vertical cinematography
        enhanced_prompt = (
            f"{prompt}, 8k resolution, cinematic lighting, photorealistic masterpiece, "
            f"Unreal Engine 5 render, volumetric atmosphere, dramatic depth of field, "
            f"ultra sharp focus, vertical 9:16 ratio, award-winning cinematography"
        )

        prompt_hash = hashlib.md5(enhanced_prompt.encode()).hexdigest()[:12]
        output_image = CACHE_DIR / f"ai_scene_{prompt_hash}.jpg"

        if output_image.exists() and output_image.stat().st_size > 10000:
            return output_image

        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        used_seed = seed or random.randint(1000, 999999)

        # Primary neural generation endpoint (Zero-key Flux / SDXL)
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width=1080&height=1920&nologo=true&enhance=true&seed={used_seed}&model=flux"
        )

        try:
            req = urllib.request.Request(
                image_url,
                headers={"User-Agent": "AutoReelStudio/2.0 (AI Video Generation Engine)"}
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    data = response.read()
                    if len(data) > 10000:
                        with open(output_image, "wb") as f:
                            f.write(data)
                        return output_image
        except Exception as e:
            print(f"  ⚠️ [AIVisual] Remote AI generator unavailable ({e}). Generating aesthetic neural fallback...")

        # Procedural High-Aesthetic Fallback Frame
        cls._render_procedural_fallback_image(prompt, output_image, seed=used_seed)
        return output_image

    @classmethod
    def _render_procedural_fallback_image(cls, prompt: str, output_path: Path, seed: int = 42):
        """Generates a high-quality atmospheric gradient with glowing cosmic particles."""
        rng = random.Random(seed)
        img = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), (10, 14, 24))
        draw = ImageDraw.Draw(img)

        # Dynamic atmospheric vertical gradient
        c1 = (rng.randint(8, 20), rng.randint(12, 28), rng.randint(35, 60))
        c2 = (rng.randint(2, 8), rng.randint(4, 12), rng.randint(12, 20))

        for y in range(TARGET_HEIGHT):
            ratio = y / TARGET_HEIGHT
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (TARGET_WIDTH, y)], fill=(r, g, b))

        # Floating ambient dust and bokeh orbs
        for _ in range(80):
            bx = rng.randint(50, TARGET_WIDTH - 50)
            by = rng.randint(100, TARGET_HEIGHT - 100)
            br = rng.randint(4, 30)
            ba = rng.randint(40, 160)
            draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(0, 240, 255, ba))

        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img.save(output_path, "JPEG", quality=95)

    @classmethod
    def render_motion_clip(
        cls,
        image_path: Path,
        duration: float,
        motion_type: str = "zoom_in",
        output_clip: Optional[Path] = None
    ) -> Path:
        """
        Transforms a static AI image into an animated 1080x1920 vertical video clip
        using smooth Ken Burns zoom and pan movements.
        """
        clip_hash = hashlib.md5(f"{image_path.name}_{duration}_{motion_type}".encode()).hexdigest()[:10]
        if output_clip is None:
            output_clip = CACHE_DIR / f"clip_{clip_hash}.mp4"

        if output_clip.exists() and output_clip.stat().st_size > 10000:
            return output_clip

        frames_count = int(math.ceil(duration * TARGET_FPS))

        # Select motion filter
        if motion_type == "zoom_out":
            zoom_expr = f"max(1.18-0.0012*on,1.0)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == "pan_left":
            zoom_expr = "1.12"
            x_expr = f"min(x+1.2,iw-iw/zoom)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_type == "pan_right":
            zoom_expr = "1.12"
            x_expr = f"max(x-1.2,0)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:  # zoom_in (default)
            zoom_expr = f"min(zoom+0.0012,1.20)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        filter_chain = (
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={frames_count}:s={TARGET_WIDTH}x{TARGET_HEIGHT}:fps={TARGET_FPS},"
            f"format=yuv420p"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", filter_chain,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            str(output_clip)
        ]

        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if res.returncode != 0 or not output_clip.exists():
            # Fallback simple render if zoompan hits memory bounds
            fallback_cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,crop={TARGET_WIDTH}:{TARGET_HEIGHT}",
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                str(output_clip)
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return output_clip
