import os
import json
import struct
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .config import (
    TARGET_WIDTH,
    TARGET_HEIGHT,
    TARGET_FPS,
    VIDEO_CODEC,
    AUDIO_CODEC,
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_BITRATE,
    VIDEO_TARGET_BITRATE,
    VIDEO_MAX_BITRATE,
    VIDEO_BUF_SIZE,
    MIN_DURATION_SECS,
    MAX_DURATION_SECS,
    MAX_FILE_SIZE_BYTES,
    SAFE_ZONE_TOP,
    SAFE_ZONE_BOTTOM,
    DEFAULT_SCALING_MODE
)

class VideoPreprocessor:
    """
    Automated video inspector, Instagram Reels compliance validator,
    and high-performance FFmpeg normalizer.
    """

    @staticmethod
    def check_faststart(filepath: Path) -> bool:
        """
        Verifies whether the MP4 file has the 'moov' atom before the 'mdat' atom.
        Required by Meta Graph API for non-blocking stream ingestion.
        """
        try:
            with open(filepath, "rb") as f:
                while True:
                    header = f.read(8)
                    if len(header) < 8:
                        break
                    size, name = struct.unpack(">I4s", header)
                    atom_name = name.decode("ascii", errors="ignore")
                    if atom_name == "moov":
                        return True
                    if atom_name == "mdat":
                        return False
                    if size == 1:
                        extended = f.read(8)
                        if len(extended) < 8:
                            break
                        size = struct.unpack(">Q", extended)[0] - 16
                    else:
                        size -= 8
                    if size < 0:
                        break
                    f.seek(size, 1)
        except Exception:
            pass
        return False

    @staticmethod
    def probe_video(video_path: Path) -> Dict[str, Any]:
        """
        Uses ffprobe to extract detailed container, stream, and codec metadata.
        """
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=index,codec_type,codec_name,profile,pix_fmt,r_frame_rate,avg_frame_rate,width,height,sample_rate,channels,bit_rate",
            "-show_entries", "format=format_name,duration,size,bit_rate",
            "-of", "json",
            str(video_path)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffprobe failed for {video_path.name}: {proc.stderr.strip()}")

        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        fmt = data.get("format", {})

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        duration = float(fmt.get("duration", 0.0))
        file_size = int(fmt.get("size", video_path.stat().st_size))
        total_bitrate = int(fmt.get("bit_rate", 0))

        fps = 0.0
        if video_stream:
            r_fps = video_stream.get("r_frame_rate", "30/1")
            try:
                num, den = map(float, r_fps.split("/"))
                fps = round(num / den, 2) if den > 0 else 30.0
            except Exception:
                fps = 30.0

        faststart = VideoPreprocessor.check_faststart(video_path)

        return {
            "path": str(video_path),
            "filename": video_path.name,
            "format_name": fmt.get("format_name", ""),
            "duration": duration,
            "file_size": file_size,
            "total_bitrate": total_bitrate,
            "faststart": faststart,
            "video": {
                "present": video_stream is not None,
                "width": video_stream.get("width") if video_stream else 0,
                "height": video_stream.get("height") if video_stream else 0,
                "aspect_ratio": f"{video_stream.get('width', 0)}:{video_stream.get('height', 0)}",
                "codec": video_stream.get("codec_name", "") if video_stream else "",
                "profile": video_stream.get("profile", "") if video_stream else "",
                "pix_fmt": video_stream.get("pix_fmt", "") if video_stream else "",
                "fps": fps
            },
            "audio": {
                "present": audio_stream is not None,
                "codec": audio_stream.get("codec_name", "") if audio_stream else "",
                "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
                "channels": int(audio_stream.get("channels", 0)) if audio_stream else 0,
                "bitrate": int(audio_stream.get("bit_rate", 0)) if (audio_stream and audio_stream.get("bit_rate")) else 0
            }
        }

    @staticmethod
    def validate_compliance(meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates extracted metadata against Meta's strict Instagram Reel requirements.
        """
        issues: List[str] = []
        warnings: List[str] = []

        dur = meta["duration"]
        if dur < MIN_DURATION_SECS:
            issues.append(f"Duration too short ({dur:.1f}s). Instagram Reels require at least {MIN_DURATION_SECS}s.")
        elif dur > MAX_DURATION_SECS:
            issues.append(f"Duration too long ({dur:.1f}s). Maximum allowed Reel length is {MAX_DURATION_SECS}s.")

        if meta["file_size"] > MAX_FILE_SIZE_BYTES:
            issues.append(f"File size exceeds 1GB limit ({meta['file_size'] / (1024*1024):.1f} MB).")
        elif meta["file_size"] > 100 * 1024 * 1024:
            warnings.append(f"File size is {meta['file_size'] / (1024*1024):.1f} MB (> 100 MB). Ingestion may take longer.")

        v = meta["video"]
        if not v["present"]:
            issues.append("No video stream found.")
        else:
            if v["width"] != TARGET_WIDTH or v["height"] != TARGET_HEIGHT:
                issues.append(f"Resolution is {v['width']}x{v['height']}, required 9:16 vertical ({TARGET_WIDTH}x{TARGET_HEIGHT}).")
            if v["codec"].lower() not in ("h264", "avc1"):
                issues.append(f"Video codec is '{v['codec']}', required H.264 (AVC).")
            if v["pix_fmt"].lower() != "yuv420p":
                issues.append(f"Pixel format is '{v['pix_fmt']}', required 4:2:0 chroma (yuv420p).")

        a = meta["audio"]
        if not a["present"]:
            issues.append("No audio track detected. Instagram Reels require an active audio track.")
        else:
            if a["codec"].lower() != "aac":
                issues.append(f"Audio codec is '{a['codec']}', required AAC.")
            if a["sample_rate"] not in (44100, 48000):
                issues.append(f"Audio sample rate is {a['sample_rate']} Hz, required 44.1 kHz or 48 kHz.")
            if a["channels"] < 2:
                issues.append(f"Audio channels count is {a['channels']}, required stereo (2 channels).")

        if not meta["faststart"]:
            issues.append("Missing faststart (moov atom not positioned at start of file for web streaming).")

        is_compliant = len(issues) == 0
        return {
            "is_compliant": is_compliant,
            "issues": issues,
            "warnings": warnings,
            "requires_transcode": not is_compliant
        }

    @staticmethod
    def normalize_video(
        input_path: Path,
        output_path: Path,
        scaling_mode: str = DEFAULT_SCALING_MODE,
        overwrite: bool = True
    ) -> Path:
        """
        Transcodes and normalizes ANY input video into exact Instagram Reel technical specifications:
        - 1080x1920 (9:16 vertical)
        - H.264 High Profile, progressive, yuv420p
        - AAC Stereo @ 48kHz, 192 kbps (synthesizes clean silence if source lacks audio)
        - 30 fps CFR, VBR target 4500k, max 5000k
        - +faststart moov atom at file header
        - Trims cleanly to 90.0s if input exceeds maximum duration
        """
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()

        if output_path.exists() and not overwrite:
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        meta = VideoPreprocessor.probe_video(input_path)

        # Build video filter based on selected scaling mode
        if scaling_mode == "crop":
            # Scale to cover 1080x1920, center crop
            vf = (
                f"scale=w={TARGET_WIDTH}:h={TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={TARGET_WIDTH}:{TARGET_HEIGHT}:(in_w-{TARGET_WIDTH})/2:(in_h-{TARGET_HEIGHT})/2,"
                f"setsar=1,fps={TARGET_FPS}"
            )
            filter_args = ["-vf", vf]
        elif scaling_mode == "blur_pad":
            # Blurred copy in background, centered sharp original in foreground
            filter_complex = (
                f"[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},boxblur=25:5[bg];"
                f"[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={TARGET_FPS}[v]"
            )
            filter_args = ["-filter_complex", filter_complex, "-map", "[v]"]
        else:
            # Default "pad" (fit entire frame, pad with black letterbox/pillarbox)
            vf = (
                f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,"
                f"setsar=1,fps={TARGET_FPS}"
            )
            filter_args = ["-vf", vf]

        cmd = ["ffmpeg", "-y", "-i", str(input_path)]

        # Handle silent input videos by generating an empty stereo 48kHz AAC track
        has_audio = meta["audio"]["present"]
        if not has_audio:
            # Inject null audio source
            cmd.extend([
                "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_SAMPLE_RATE}"
            ])

        cmd.extend(filter_args)

        # Video encoding parameters
        cmd.extend([
            "-c:v", "libx264",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-r", str(TARGET_FPS),
            "-b:v", VIDEO_TARGET_BITRATE,
            "-maxrate", VIDEO_MAX_BITRATE,
            "-bufsize", VIDEO_BUF_SIZE,
        ])

        # Audio encoding parameters
        if has_audio:
            if scaling_mode == "blur_pad":
                cmd.extend(["-map", "0:a"])
            cmd.extend([
                "-c:a", "aac",
                "-b:a", AUDIO_BITRATE,
                "-ar", str(AUDIO_SAMPLE_RATE),
                "-ac", str(AUDIO_CHANNELS)
            ])
        else:
            # Map null audio track
            cmd.extend([
                "-map", "1:a",
                "-c:a", "aac",
                "-b:a", AUDIO_BITRATE,
                "-ar", str(AUDIO_SAMPLE_RATE),
                "-ac", str(AUDIO_CHANNELS),
                "-shortest"
            ])

        # Duration constraint: enforce max 90.0 seconds
        if meta["duration"] > MAX_DURATION_SECS:
            cmd.extend(["-t", str(MAX_DURATION_SECS)])

        # Faststart for immediate web/API ingestion
        cmd.extend([
            "-movflags", "+faststart",
            str(output_path)
        ])

        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg normalization failed for {input_path.name}: {proc.stderr[-300:]}")

        # Post-validation confirmation
        norm_meta = VideoPreprocessor.probe_video(output_path)
        check = VideoPreprocessor.validate_compliance(norm_meta)
        if not check["is_compliant"]:
            raise RuntimeError(f"Normalized file failed compliance check: {', '.join(check['issues'])}")

        return output_path

    @staticmethod
    def render_safe_zone_preview(video_path: Path, output_preview_path: Path) -> Path:
        """
        Renders a debug visual frame with Instagram Reels mobile UI overlays,
        illustrating the top 220px danger zone and bottom 380px danger zone.
        """
        video_path = Path(video_path).resolve()
        output_preview_path = Path(output_preview_path).resolve()

        filter_str = (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT},"
            # Top UI Danger Zone (220px)
            f"drawbox=x=0:y=0:w={TARGET_WIDTH}:h={SAFE_ZONE_TOP}:color=red@0.35:t=fill,"
            f"drawbox=x=0:y=0:w={TARGET_WIDTH}:h={SAFE_ZONE_TOP}:color=red@0.9:t=2,"
            f"drawtext=text='INSTAGRAM UI DANGER ZONE (Top 220px - Header / Status)':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=90,"
            # Safe Content Zone Guide
            f"drawbox=x=0:y={SAFE_ZONE_TOP}:w={TARGET_WIDTH}:h={TARGET_HEIGHT-SAFE_ZONE_TOP-SAFE_ZONE_BOTTOM}:color=green@0.7:t=2,"
            f"drawtext=text='SAFE DISPLAY CONTENT ZONE (1080 x 1320 px)':fontsize=36:fontcolor=green:x=(w-text_w)/2:y=260,"
            # Bottom UI Danger Zone (380px)
            f"drawbox=x=0:y={TARGET_HEIGHT-SAFE_ZONE_BOTTOM}:w={TARGET_WIDTH}:h={SAFE_ZONE_BOTTOM}:color=red@0.35:t=fill,"
            f"drawbox=x=0:y={TARGET_HEIGHT-SAFE_ZONE_BOTTOM}:w={TARGET_WIDTH}:h={SAFE_ZONE_BOTTOM}:color=red@0.9:t=2,"
            f"drawtext=text='INSTAGRAM UI DANGER ZONE (Bottom 380px - Audio / Caption / Icons)':fontsize=30:fontcolor=white:x=(w-text_w)/2:y={TARGET_HEIGHT-200}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-ss", "0.5",
            "-i", str(video_path),
            "-vf", filter_str,
            "-vframes", "1",
            str(output_preview_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        return output_preview_path

