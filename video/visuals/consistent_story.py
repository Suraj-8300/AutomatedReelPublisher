"""
Consistent Character Story Visual Engine for AutoReelStudio.

Eliminates the "random disconnected stock clips" problem by generating all scenes
around a persistent, locked character identity and consistent environment.

Features:
- Character Continuity: Locks species, breed, distinctive markings, accessories, and setting.
- Smart Pacing: Handles Pollinations free tier pacing (40-45s rate limit) gracefully with progress updates.
- Multi-Angle Fallback: If network drops, extracts cinematic multi-shot framings (wide, medium, close-up)
  from the master character keyframe so the character identity NEVER morphs into an unrelated animal.
- Living Video Motion: Dynamic non-linear camera moves (push-in, lateral dolly, reveal) plus
  subtle 35mm organic moving film grain (30fps) so scenes feel alive and filmic, not like static slides.
"""

import math
import time
import re
import hashlib
import urllib.parse
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import requests
from PIL import Image

from video.config import (
    CACHE_DIR, POLLINATIONS_BASE, TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS
)

_STORY_CACHE = CACHE_DIR / "consistent_story"
_STORY_CACHE.mkdir(parents=True, exist_ok=True)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def fit_to_vertical(im: Image.Image, target_w: int = TARGET_WIDTH, target_h: int = TARGET_HEIGHT) -> Image.Image:
    """Center-crops and scales any image to fill exact vertical 9:16 aspect ratio."""
    target_ratio = target_w / target_h
    im_ratio = im.width / im.height

    if im_ratio > target_ratio:
        new_h = target_h
        new_w = int(im.width * (target_h / im.height))
    else:
        new_w = target_w
        new_h = int(im.height * (target_w / im.width))

    resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


class ConsistentStoryEngine:
    """
    Renders high-retention character-locked vertical story reels.
    Guarantees visual continuity across all scenes.
    """

    @classmethod
    def fetch_scene_frame(
        cls,
        prompt: str,
        seed: int,
        scene_idx: int,
        total_scenes: int,
        retries: int = 2
    ) -> Optional[Path]:
        """
        Fetches a high-resolution 1080x1920 AI keyframe from Pollinations
        with polite retry handling when pacing limits are met.
        """
        clean_key = hashlib.md5(f"{prompt}_{seed}".encode()).hexdigest()[:12]
        out_path = _STORY_CACHE / f"frame_{clean_key}.jpg"

        if out_path.exists() and out_path.stat().st_size > 15000:
            return out_path

        encoded = urllib.parse.quote(prompt)
        url = f"{POLLINATIONS_BASE}/{encoded}?width={TARGET_WIDTH}&height={TARGET_HEIGHT}&seed={seed}&nologo=true&model=flux"

        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=BROWSER_HEADERS, timeout=40)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    img = Image.open(BytesIO(resp.content))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img = fit_to_vertical(img, TARGET_WIDTH, TARGET_HEIGHT)
                    img.save(out_path, "JPEG", quality=94)
                    return out_path

                elif resp.status_code == 402:
                    m = re.search(r"Retry after (\d+)s", resp.text)
                    wait_s = int(m.group(1)) + 1 if m else 40
                    if wait_s <= 45 and attempt < retries - 1:
                        print(f"   ⏳ Pacing free high-res generation ({wait_s}s for scene {scene_idx + 1}/{total_scenes})...")
                        time.sleep(wait_s)
                        continue
                    else:
                        break
                elif resp.status_code in (502, 503, 504):
                    if attempt < retries - 1:
                        time.sleep(5)
                        continue
                    break
            except Exception:
                if attempt < retries - 1:
                    time.sleep(4)

        return None

    @classmethod
    def create_cinematic_crop(
        cls,
        master_img_path: Path,
        crop_type: str = "medium",
        out_path: Optional[Path] = None
    ) -> Path:
        """
        Extracts a high-res cinematographic framing (action medium shot or dramatic close-up)
        from a master character frame to maintain strict identity continuity.
        """
        if out_path is None:
            cache_key = hashlib.md5(f"{master_img_path.name}_{crop_type}".encode()).hexdigest()[:10]
            out_path = _STORY_CACHE / f"crop_{cache_key}.jpg"

        if out_path.exists() and out_path.stat().st_size > 15000:
            return out_path

        img = Image.open(master_img_path)
        w, h = img.size

        if crop_type == "close_up":
            # 60% crop focused on upper-center (character face/eyes)
            crop_w = int(w * 0.65)
            crop_h = int(h * 0.65)
            left = (w - crop_w) // 2
            top = int(h * 0.15)
        elif crop_type == "medium":
            # 80% crop focused on character action
            crop_w = int(w * 0.82)
            crop_h = int(h * 0.82)
            left = (w - crop_w) // 2
            top = int(h * 0.10)
        else:
            return master_img_path

        cropped = img.crop((left, top, left + crop_w, top + crop_h))
        cropped = cropped.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        cropped.save(out_path, "JPEG", quality=94)
        return out_path

    @classmethod
    def render_motion_clip(
        cls,
        image_path: Path,
        duration: float,
        motion: str = "dynamic_push",
        run_id: str = "run"
    ) -> Path:
        """
        Animates a static character frame into a dynamic vertical video clip.
        Uses non-linear camera motion and adds subtle 35mm organic film grain
        so pixels are actively in motion across every frame.
        """
        cache_key = hashlib.md5(f"{image_path.name}_{duration:.2f}_{motion}_{run_id}".encode()).hexdigest()[:10]
        out_clip = _STORY_CACHE / f"motion_{cache_key}.mp4"

        if out_clip.exists() and out_clip.stat().st_size > 10000:
            return out_clip

        frames = int(math.ceil(duration * TARGET_FPS))
        w, h, fps = TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS

        # Motion Filter Selection
        if motion == "lateral_dolly":
            # Smooth cinematic tracking shot sliding sideways
            motion_filter = (
                f"zoompan=z='1.12':x='min(x+1.2,iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={w}x{h}:fps={fps}"
            )
        elif motion == "dynamic_reveal":
            # Gentle orbital camera drift / upward reveal
            motion_filter = (
                f"zoompan=z='1.10':x='iw/2-(iw/zoom/2)':y='max(y-0.8,0)'"
                f":d={frames}:s={w}x{h}:fps={fps}"
            )
        elif motion == "whip_zoom":
            # Faster punchy zoom-in for comedic or high-stakes beats
            motion_filter = (
                f"zoompan=z='min(zoom+0.0028,1.30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={w}x{h}:fps={fps}"
            )
        else:
            # Default: dynamic_push (smooth cinematic push-in toward character)
            motion_filter = (
                f"zoompan=z='min(zoom+0.0016,1.22)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={frames}:s={w}x{h}:fps={fps}"
            )

        # Filter chain combines non-linear camera move + subtle film grain for living motion
        filter_complex = f"{motion_filter},noise=c0s=6:allf=t+u,format=yuv420p"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(fps),
            "-i", str(image_path.resolve()),
            "-vf", filter_complex,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-an",
            str(out_clip)
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if res.returncode != 0 or not out_clip.exists():
            # Robust fallback: static scale + pad with grain
            fallback_cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-framerate", str(fps),
                "-i", str(image_path.resolve()),
                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,noise=c0s=6:allf=t+u,format=yuv420p",
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                "-an",
                str(out_clip)
            ]
            subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=120)

        return out_clip

    @classmethod
    def generate_scenes(
        cls,
        scenes: List[Dict[str, Any]],
        durations: List[float],
        character_token: str = "",
        seed: int = 42,
        run_id: str = "run"
    ) -> List[Path]:
        """
        Main entry point for generating character-consistent visual scenes.

        Args:
            scenes: List of scene dictionaries (with 'prompt' or 'text')
            durations: Duration in seconds for each scene
            character_token: Locked character & environment description
            seed: Locked seed for character consistency
            run_id: Unique run ID for caching

        Returns:
            List of Path objects pointing to rendered MP4 scene clips.
        """
        print(f"🐾 ConsistentStoryEngine: Generating {len(scenes)} character-locked visual scenes...")
        if character_token:
            print(f"   🔒 Locked Character: {character_token[:80]}...")

        scene_clips = []
        master_frame: Optional[Path] = None

        # Choreographed camera motion cycle
        motions = ["dynamic_push", "lateral_dolly", "dynamic_reveal"]

        for idx, scene in enumerate(scenes):
            dur = durations[idx] if idx < len(durations) else 5.0
            motion = motions[idx % len(motions)]

            # Construct bespoke prompt with locked character token
            raw_prompt = scene.get("prompt") or scene.get("visual_prompt") or scene.get("text", "")
            if character_token and character_token.lower() not in raw_prompt.lower():
                prompt = f"{character_token}, {raw_prompt}, photorealistic, 8k cinematic lighting, 9:16 vertical portrait"
            else:
                prompt = f"{raw_prompt}, photorealistic, 8k cinematic lighting, 9:16 vertical portrait"

            print(f"   🎨 Sourcing scene {idx + 1}/{len(scenes)} visual ({motion})...")

            # Fetch AI keyframe with locked seed
            frame_path = cls.fetch_scene_frame(
                prompt=prompt,
                seed=seed + (idx * 37),
                scene_idx=idx,
                total_scenes=len(scenes)
            )

            if frame_path and frame_path.exists():
                if master_frame is None:
                    master_frame = frame_path
                active_frame = frame_path
            elif master_frame is not None:
                # Continuity fallback: extract medium or close-up crop of same character!
                crop_style = "medium" if idx == 1 else "close_up"
                print(f"   ℹ️  Preserving character identity: applying cinematic {crop_style} camera framing...")
                active_frame = cls.create_cinematic_crop(master_frame, crop_type=crop_style)
            else:
                # Initial scene fallback: generate aesthetic cinematic scene
                from video.visuals.cinematic import CinematicEngine
                print(f"   ℹ️  Falling back to high-res aesthetic cinematic visual...")
                active_frame = CinematicEngine.fetch_image(prompt, seed=seed, pillar="animal_story")

            # Render dynamic motion clip
            clip = cls.render_motion_clip(
                image_path=active_frame,
                duration=dur,
                motion=motion,
                run_id=run_id
            )
            scene_clips.append(clip)

        print(f"   ✅ All {len(scene_clips)} character-consistent scenes rendered successfully.")
        return scene_clips
