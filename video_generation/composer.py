"""
Full-Screen 9:16 Video Compositor for AutoReelStudio.
Concatenates animated scene clips, burns ASS subtitles, merges master audio,
and produces the master 1080x1920 @ 30fps MP4 video.
"""

import os
import subprocess
import hashlib
from pathlib import Path
from typing import List, Optional

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class VideoComposer:
    """Composites visual scenes, audio, and subtitles into a finished 1080x1920 video."""

    @classmethod
    def assemble_reel(
        cls,
        scene_clips: List[Path],
        master_audio_path: Path,
        subtitles_path: Path,
        output_filename: str,
        total_duration: float
    ) -> Path:
        """
        Stitches multiple visual scene clips, overlays audio, and burns ASS subtitles.
        """
        out_mp4 = OUTPUT_DIR / output_filename

        # Create concat demuxer file
        concat_list = CACHE_DIR / f"concat_{hashlib.md5(output_filename.encode()).hexdigest()[:8]}.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                f.write(f"file '{clip.resolve()}'\n")

        # Concat scenes into raw video stream
        merged_video = CACHE_DIR / f"merged_{hashlib.md5(output_filename.encode()).hexdigest()[:8]}.mp4"
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            str(merged_video)
        ]
        subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Escape path for subtitles filter in FFmpeg
        sub_escaped = str(subtitles_path.resolve()).replace("\\", "/").replace(":", "\\:")

        # Final assembly with subtitles and mastered audio
        final_cmd = [
            "ffmpeg", "-y",
            "-i", str(merged_video),
            "-i", str(master_audio_path),
            "-vf", f"subtitles='{sub_escaped}'",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_duration:.3f}",
            str(out_mp4)
        ]

        res = subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if res.returncode != 0 or not out_mp4.exists():
            # Fallback without subtitle filter if libass error occurs
            fallback_cmd = [
                "ffmpeg", "-y",
                "-i", str(merged_video),
                "-i", str(master_audio_path),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{total_duration:.3f}",
                str(out_mp4)
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return out_mp4
