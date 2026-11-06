"""
Manim Animator — generates and renders Manim Community animation scripts locally.
Used for 'mechanical' and 'explainer' content pillars.
Produces stunning 3Blue1Brown-style educational animations completely free.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from video.config import CACHE_DIR, TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS

_MANIM_CACHE = CACHE_DIR / "manim"
_MANIM_CACHE.mkdir(parents=True, exist_ok=True)


def _manim_available() -> bool:
    """Checks if the manim CLI is installed and callable."""
    return shutil.which("manim") is not None


class ManimAnimator:
    """
    Runs Manim Community to render animated diagram videos locally.
    Falls back to a Pillow-based placeholder if Manim is not installed.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if manim CLI is installed on this system."""
        return _manim_available()

    @classmethod
    def render(
        cls,
        manim_code: str,
        scene_class: str = "AutoReelScene",
        output_path: Optional[Path] = None,
        quality: str = "h",          # h = 1080p 60fps, m = 720p 30fps, l = 480p 15fps
    ) -> Path:
        """
        Writes the Manim Python code to a temp file, renders it, and returns
        the path to the rendered MP4 video clip.
        """
        # Create a unique working directory for this render
        work_dir = _MANIM_CACHE / f"render_{hash(manim_code) & 0xFFFFFF:06x}"
        work_dir.mkdir(parents=True, exist_ok=True)

        script_path = work_dir / "scene.py"
        script_path.write_text(manim_code, encoding="utf-8")

        if output_path is None:
            output_path = work_dir / "output.mp4"

        if not _manim_available():
            print("[ManimAnimator] ⚠️  Manim not found. Using placeholder clip.")
            print("[ManimAnimator] Install with: pip install manim")
            return cls._placeholder_clip(output_path)

        # Render with manim CLI
        # --media_dir controls where manim puts its output
        media_dir = work_dir / "media"
        cmd = [
            "manim",
            f"-q{quality}",
            "--format", "mp4",
            "--media_dir", str(media_dir),
            "--disable_caching",
            str(script_path),
            scene_class,
        ]

        print(f"[ManimAnimator] 🎬 Rendering {scene_class} ...")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=300,  # 5 min max
            )
            if result.returncode != 0:
                print(f"[ManimAnimator] Manim stderr:\n{result.stderr[-500:]}")
        except subprocess.TimeoutExpired:
            print("[ManimAnimator] ⚠️  Manim render timed out.")
            return cls._placeholder_clip(output_path)
        except Exception as e:
            print(f"[ManimAnimator] ⚠️  Manim render error: {e}")
            return cls._placeholder_clip(output_path)

        # Find the rendered MP4 file
        rendered = cls._find_rendered_mp4(media_dir, scene_class)
        if rendered:
            # Reformat to exact 9:16 1080x1920 using FFmpeg
            return cls._reformat_to_vertical(rendered, output_path)
        else:
            print("[ManimAnimator] ⚠️  Rendered file not found, using placeholder.")
            return cls._placeholder_clip(output_path)

    @staticmethod
    def _find_rendered_mp4(media_dir: Path, scene_class: str) -> Optional[Path]:
        """Searches for Manim's rendered MP4 output file."""
        if not media_dir.exists():
            return None
        # Manim outputs to media/videos/scene/<quality>/SceneClass.mp4
        for mp4 in media_dir.rglob("*.mp4"):
            if scene_class.lower() in mp4.stem.lower() or True:
                return mp4
        return None

    @staticmethod
    def _reformat_to_vertical(src: Path, dst: Path) -> Path:
        """Reformats a Manim-rendered video to exact 1080x1920 9:16 for Reels."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
                   f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(dst)
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and dst.exists():
            return dst
        # If reformat fails, use original
        shutil.copy2(src, dst)
        return dst

    @staticmethod
    def _placeholder_clip(output_path: Path, duration: float = 30.0) -> Path:
        """
        Generates a styled placeholder video clip (black with text) using FFmpeg.
        Used when Manim is not installed.
        """
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x0a0a0f:size={TARGET_WIDTH}x{TARGET_HEIGHT}:rate={TARGET_FPS}:duration={duration}",
            "-vf", (
                "drawtext=text='Install manim for animated diagrams':fontsize=48:"
                "fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:fontfile=/usr/share/fonts/"
                "liberation-sans-fonts/LiberationSans-Bold.ttf"
            ),
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        # Fallback drawtext without custom font if font not found
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            simple_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:size={TARGET_WIDTH}x{TARGET_HEIGHT}:rate={TARGET_FPS}:duration={duration}",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                str(output_path)
            ]
            subprocess.run(simple_cmd, capture_output=True)
        return output_path
