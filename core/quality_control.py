import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import WIDTH, HEIGHT

class QualityControlEngine:
    """
    Automated Multi-Stage Reel Quality Control Engine.
    Inspects visual geometry, audio health, content pacing, and Meta publishing compliance
    prior to marking any video as production-ready.
    """

    @staticmethod
    def audit_video(video_path: Path, storyboard: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs comprehensive technical and creative QC checks on a rendered video.
        """
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            return {
                "passed": False,
                "overall_status": "FAILED",
                "score": 0,
                "errors": [f"File does not exist: {video_path}"]
            }

        errors = []
        warnings = []
        checks = {}

        # 1. FFprobe Stream Analysis
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height,codec_name,r_frame_rate,channels,sample_rate,duration:format=duration,size,bit_rate",
            "-of", "json",
            str(video_path)
        ]
        proc = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return {
                "passed": False,
                "overall_status": "FAILED",
                "score": 0,
                "errors": [f"ffprobe failed to inspect container: {proc.stderr}"]
            }

        try:
            probe_data = json.loads(proc.stdout)
        except Exception:
            probe_data = {}

        streams = probe_data.get("streams", [])
        v_stream = next((s for s in streams if s.get("width") is not None), None)
        a_stream = next((s for s in streams if s.get("channels") is not None), None)
        format_info = probe_data.get("format", {})

        # 2. Visual Quality Checks
        if not v_stream:
            errors.append("No video stream found in container")
            checks["visual_stream"] = False
        else:
            w = int(v_stream.get("width", 0))
            h = int(v_stream.get("height", 0))
            v_codec = v_stream.get("codec_name", "")

            # Aspect Ratio Check (1080x1920 9:16)
            if w == WIDTH and h == HEIGHT:
                checks["resolution_1080x1920"] = True
                checks["aspect_ratio_9_16"] = True
            else:
                ratio = w / h if h > 0 else 0
                if abs(ratio - (9.0 / 16.0)) < 0.02:
                    checks["resolution_1080x1920"] = False
                    checks["aspect_ratio_9_16"] = True
                    warnings.append(f"Aspect ratio is 9:16 but resolution is {w}x{h} (target: {WIDTH}x{HEIGHT})")
                else:
                    checks["resolution_1080x1920"] = False
                    checks["aspect_ratio_9_16"] = False
                    errors.append(f"Non-compliant aspect ratio: {w}x{h} (required: 1080x1920 9:16)")

            # Video Codec
            if v_codec == "h264":
                checks["video_codec_h264"] = True
            else:
                checks["video_codec_h264"] = False
                warnings.append(f"Video codec is {v_codec} (recommended: h264)")

        # 3. Audio Quality Checks
        if not a_stream:
            errors.append("No audio stream found in container")
            checks["audio_stream"] = False
        else:
            a_codec = a_stream.get("codec_name", "")
            channels = int(a_stream.get("channels", 0))
            sample_rate = int(a_stream.get("sample_rate", 0))

            if a_codec == "aac":
                checks["audio_codec_aac"] = True
            else:
                checks["audio_codec_aac"] = False
                warnings.append(f"Audio codec is {a_codec} (recommended: aac)")

            if channels == 2:
                checks["audio_stereo"] = True
            else:
                checks["audio_stereo"] = False
                warnings.append(f"Audio channels: {channels} (recommended: 2 stereo)")

            if sample_rate == 48000:
                checks["audio_sample_rate_48k"] = True
            else:
                checks["audio_sample_rate_48k"] = False
                warnings.append(f"Audio sample rate: {sample_rate}Hz (recommended: 48000Hz)")

        # 4. Container Duration & File Size
        dur = float(format_info.get("duration", 0.0))
        size_bytes = int(format_info.get("size", 0))

        if 5.0 <= dur <= 95.0:
            checks["duration_compliant"] = True
        else:
            checks["duration_compliant"] = False
            errors.append(f"Reel duration {dur:.1f}s outside Instagram bounds [5s - 90s]")

        if size_bytes > 50000:
            checks["file_size_valid"] = True
        else:
            checks["file_size_valid"] = False
            errors.append("File size too small (possible corrupted render)")

        # 5. Faststart Moov Atom Check (Web streaming readiness)
        try:
            with open(video_path, "rb") as f:
                header = f.read(1024 * 64)
                has_faststart = b"moov" in header
                checks["faststart_moov_atom"] = has_faststart
                if not has_faststart:
                    warnings.append("Moov atom not located at file head; instant streaming may be delayed")
        except Exception:
            checks["faststart_moov_atom"] = False

        # 6. Content QC Check (if storyboard provided)
        if storyboard:
            script = storyboard.get("script", "")
            words = script.split()
            checks["hook_present"] = bool(storyboard.get("hook"))
            checks["scenes_count"] = len(storyboard.get("scenes", []))
            checks["genre_labeled"] = bool(storyboard.get("genre"))

            # Pacing ratio (words per second)
            wps = len(words) / dur if dur > 0 else 0
            if 1.8 <= wps <= 3.8:
                checks["pacing_optimal"] = True
            else:
                checks["pacing_optimal"] = False
                warnings.append(f"Speech pacing is {wps:.2f} words/sec (ideal: 2.2 - 3.2)")

        # Scoring
        total_checks = len(checks)
        passed_checks = sum(1 for v in checks.values() if v is True)
        score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
        passed = (len(errors) == 0) and (score >= 75)

        return {
            "passed": passed,
            "overall_status": "PASSED" if passed else "FAILED",
            "score": score,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "duration": dur,
            "size_mb": round(size_bytes / (1024 * 1024), 2)
        }

