"""
Ken Burns Camera Motion Engine for AutoReelStudio.
Animates static AI images into cinematic 9:16 video clips using FFmpeg
zoompan filter with smooth zoom-in, zoom-out, pan-left, pan-right, and
drift motions. Produces documentary-quality camera movement.
"""

import math
import hashlib
import subprocess
from pathlib import Path
from typing import Optional, List

from video.config import CACHE_DIR, TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS

_CLIP_CACHE = CACHE_DIR / "clips"
_CLIP_CACHE.mkdir(parents=True, exist_ok=True)

MOTION_TYPES = ["zoom_in", "zoom_out", "pan_left", "pan_right", "drift_up", "drift_down"]


def _get_motion_filter(motion: str, frames: int) -> str:
    """Returns an FFmpeg zoompan filter expression for the given motion type."""
    w, h, fps = TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS

    if motion == "zoom_in":
        return (
            f"zoompan=z='min(zoom+0.0012,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif motion == "zoom_out":
        return (
            f"zoompan=z='max(1.25-0.0012*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif motion == "pan_left":
        return (
            f"zoompan=z='1.10':x='min(x+0.8,iw-iw/zoom)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif motion == "pan_right":
        return (
            f"zoompan=z='1.10':x='max(x-0.8,0)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif motion == "drift_up":
        return (
            f"zoompan=z='1.08':x='iw/2-(iw/zoom/2)':y='min(y+0.5,ih-ih/zoom)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif motion == "drift_down":
        return (
            f"zoompan=z='1.08':x='iw/2-(iw/zoom/2)':y='max(y-0.5,0)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    else:
        # Default: gentle zoom-in
        return (
            f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )


class KenBurnsEngine:
    """
    Converts static images into animated video clips with cinematic camera motion.
    Automatically cycles through motion types for visual variety across scenes.
    """

    @classmethod
    def animate_image(
        cls,
        image_path: Path,
        duration: float,
        motion: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Animates a single image with Ken Burns motion.

        Args:
            image_path: Path to source image (JPEG/PNG)
            duration: Clip duration in seconds
            motion: Motion type (zoom_in/zoom_out/pan_left/pan_right/drift_up/drift_down)
            output_path: Where to save the MP4 clip

        Returns:
            Path to the rendered MP4 clip
        """
        if motion is None:
            # Deterministic motion selection based on image content
            motion = MOTION_TYPES[hash(str(image_path)) % len(MOTION_TYPES)]

        cache_key = hashlib.md5(f"{image_path.name}_{duration:.1f}_{motion}".encode()).hexdigest()[:10]
        if output_path is None:
            output_path = _CLIP_CACHE / f"clip_{cache_key}.mp4"

        if output_path.exists() and output_path.stat().st_size > 10000:
            return output_path

        frames = int(math.ceil(duration * TARGET_FPS))
        motion_filter = _get_motion_filter(motion, frames)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(TARGET_FPS),
            "-i", str(image_path.resolve()),
            "-vf", f"{motion_filter},format=yuv420p",
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-an",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=120)

        if result.returncode != 0 or not output_path.exists():
            # Fallback: static image clip with no motion
            fallback_cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-framerate", str(TARGET_FPS),
                "-i", str(image_path.resolve()),
                "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
                       f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                "-an",
                str(output_path),
            ]
            subprocess.run(fallback_cmd, capture_output=True, timeout=120)

        return output_path

    @classmethod
    def animate_scenes(
        cls,
        image_paths: List[Path],
        durations: List[float],
    ) -> List[Path]:
        """
        Animates a list of images with varied Ken Burns motions.
        Returns list of MP4 clip paths in the same order.
        """
        clips = []
        for i, (img_path, dur) in enumerate(zip(image_paths, durations)):
            # Cycle through motions for variety
            motion = MOTION_TYPES[i % len(MOTION_TYPES)]
            print(f"  🎥 Animating scene {i+1}/{len(image_paths)} ({motion})...")
            clip = cls.animate_image(img_path, duration=dur, motion=motion)
            clips.append(clip)
        return clips
