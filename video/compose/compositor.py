"""
Master FFmpeg Video Compositor for AutoReelStudio.
Concatenates visual clips, overlays the mixed audio track, burns ASS subtitles,
and produces a final 1080x1920 9:16 MP4 optimized for CDN streaming.
"""

import hashlib
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional

from video.config import (
    CACHE_DIR, OUTPUT_DIR,
    TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS,
    VIDEO_CRF, VIDEO_PRESET
)

_WORK_CACHE = CACHE_DIR / "compose"
_WORK_CACHE.mkdir(parents=True, exist_ok=True)


class Compositor:
    """
    Assembles a finished 9:16 Reel/Short from scene clips, audio, and subtitles.
    """

    @classmethod
    def assemble(
        cls,
        scene_clips: List[Path],
        audio_path: Path,
        subtitles_path: Optional[Path],
        output_filename: Optional[str] = None,
        total_duration: Optional[float] = None,
        apply_faststart: bool = True,
    ) -> Path:
        """
        Full pipeline assembly:
        1. Concatenates scene video clips
        2. Overlays master audio (voice + music mix)
        3. Burns ASS subtitles
        4. Re-encodes with faststart for CDN streaming

        Returns the final MP4 path in the output/ directory.
        """
        if output_filename is None:
            output_filename = f"reel_{uuid.uuid4().hex[:10]}.mp4"

        out_mp4 = OUTPUT_DIR / output_filename
        run_id = hashlib.md5(output_filename.encode()).hexdigest()[:8]

        # Step 1: Concatenate scene clips
        concat_path = cls._concat_clips(scene_clips, run_id)

        # Step 2: Merge audio + video + optional subtitles
        raw_out = _WORK_CACHE / f"raw_{run_id}.mp4"
        cls._merge_audio_video(concat_path, audio_path, subtitles_path, raw_out, total_duration)

        # Step 3: Faststart moov-atom relocation for CDN streaming
        if apply_faststart:
            cls._apply_faststart(raw_out, out_mp4)
        else:
            import shutil
            shutil.move(str(raw_out), str(out_mp4))

        # Cleanup intermediate files
        for tmp in [concat_path, raw_out]:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass

        return out_mp4

    @classmethod
    def _concat_clips(cls, clips: List[Path], run_id: str) -> Path:
        """Concatenates multiple video clips using FFmpeg concat demuxer."""
        concat_list = _WORK_CACHE / f"concat_{run_id}.txt"
        merged = _WORK_CACHE / f"merged_{run_id}.mp4"

        # Write the concat list
        with open(concat_list, "w", encoding="utf-8") as f:
            for clip in clips:
                f.write(f"file '{clip.resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-an",
            str(merged),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)

        if result.returncode != 0 or not merged.exists():
            # Fallback: use the first clip only
            import shutil
            shutil.copy2(clips[0], merged)

        concat_list.unlink(missing_ok=True)
        return merged

    @classmethod
    def _merge_audio_video(
        cls,
        video_path: Path,
        audio_path: Path,
        subtitles_path: Optional[Path],
        output_path: Path,
        total_duration: Optional[float],
    ) -> None:
        """Merges video + audio and optionally burns subtitles."""
        vf_chain = []

        # Subtitle burn-in
        if subtitles_path and subtitles_path.exists():
            # Escape path for FFmpeg subtitles filter
            sub_escaped = str(subtitles_path.resolve()).replace("\\", "/").replace(":", "\\:")
            vf_chain.append(f"subtitles='{sub_escaped}'")

        # Guarantee strict broadcast yuv420p chroma with TV color range (no yuvj420p)
        vf_chain.append("scale=in_range=pc:out_range=tv,format=yuv420p")
        vf = ",".join(vf_chain)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-shortest",
        ]

        if total_duration:
            cmd += ["-t", f"{total_duration:.3f}"]

        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, timeout=300)

        if result.returncode != 0 or not output_path.exists():
            print(f"  ⚠️  Primary composite failed ({result.returncode}), attempting fallback without subtitles...")
            fallback_cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p",
                "-c:v", "libx264",
                "-preset", VIDEO_PRESET,
                "-crf", str(VIDEO_CRF),
                "-pix_fmt", "yuv420p",
                "-color_range", "tv",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                "-ac", "2",
                "-shortest",
                str(output_path),
            ]
            fb_res = subprocess.run(fallback_cmd, capture_output=True, timeout=300)
            if not output_path.exists():
                err_msg = fb_res.stderr.decode(errors="ignore") if fb_res.stderr else result.stderr.decode(errors="ignore")
                raise RuntimeError(f"FFmpeg compositing failed: {err_msg[:400]}")

    @staticmethod
    def _apply_faststart(src: Path, dst: Path) -> None:
        """Relocates the moov atom to the file head for instant CDN streaming."""
        if not src.exists():
            raise FileNotFoundError(f"Source file for faststart does not exist: {src}")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-c", "copy",
            "-movflags", "+faststart",
            str(dst),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode != 0 or not dst.exists():
            import shutil
            shutil.copy2(src, dst)
