"""
AI Video Analyzer & Understanding Engine for AutoReelStudio.

Reads uploaded video files directly using Gemini Multimodal / Video Understanding.
Watches the visual frames and listens to audio/speech to automatically generate:
- Comprehensive visual summary and audio/speech transcript
- High-CTR Title for YouTube Shorts & Instagram
- Scroll-stopping Hook line
- Tailored Instagram Caption (with emojis, narrative spacing, CTA & hashtag block)
- 15-20 viral & niche hashtags
- YouTube Shorts Title & SEO-optimized Description
"""

import os
import json
import time
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image

from video.config import GEMINI_API_KEY, CACHE_DIR, OUTPUT_DIR
from video.cdn_optimizer import CDNOptimizer

_THUMB_DIR = CACHE_DIR / "thumbnails"
_THUMB_DIR.mkdir(parents=True, exist_ok=True)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extracts valid JSON dictionary from model response text."""
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


class VideoAnalyzer:
    """Understands uploaded video content and generates social distribution metadata."""

    @classmethod
    def generate_thumbnail(cls, video_path: Path, output_path: Optional[Path] = None) -> Path:
        """Extracts a crisp poster frame thumbnail from the video."""
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_thumb.jpg"

        if output_path.exists() and output_path.stat().st_size > 5000:
            return output_path

        # Try to capture at 1.0 second or middle of short video
        cmd = [
            "ffmpeg", "-y",
            "-ss", "00:00:01.000",
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0 or not output_path.exists():
            # Fallback to frame 0
            cmd_fb = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_path)
            ]
            subprocess.run(cmd_fb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return output_path

    @classmethod
    def extract_keyframes(cls, video_path: Path, count: int = 6) -> List[Path]:
        """Extracts evenly spaced keyframes across the video duration for vision analysis."""
        probe = CDNOptimizer.probe_video(video_path)
        duration = probe.get("duration", 10.0) if probe.get("valid") else 10.0
        duration = max(duration, 1.0)

        step = duration / (count + 1)
        keyframe_paths = []

        frame_dir = CACHE_DIR / "keyframes" / video_path.stem
        frame_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, count + 1):
            ts = i * step
            out_file = frame_dir / f"frame_{i:02d}.jpg"
            if not out_file.exists():
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{ts:.2f}",
                    "-i", str(video_path),
                    "-vf", "scale=540:960:force_original_aspect_ratio=decrease",
                    "-vframes", "1",
                    "-q:v", "3",
                    str(out_file)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if out_file.exists() and out_file.stat().st_size > 2000:
                keyframe_paths.append(out_file)

        return keyframe_paths

    @classmethod
    def analyze_video(
        cls,
        video_path: Path,
        custom_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reads the video file, analyzes visuals and speech, and writes companion metadata JSON.
        """
        video_path = Path(video_path).resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        print(f"\n🔍 VideoAnalyzer: Reading video '{video_path.name}'...")

        # 1. Probe Technical Specs
        probe = CDNOptimizer.probe_video(video_path)
        thumb_path = cls.generate_thumbnail(video_path)

        metadata: Dict[str, Any] = {
            "filename": video_path.name,
            "path": str(video_path),
            "size_mb": probe.get("size_mb", round(video_path.stat().st_size / (1024 * 1024), 2)),
            "duration": probe.get("duration", 0.0),
            "width": probe.get("video", {}).get("width", 1080),
            "height": probe.get("video", {}).get("height", 1920),
            "codec": probe.get("video", {}).get("codec", "h264"),
            "thumbnail": f"/media/output/{thumb_path.name}" if thumb_path.exists() else None,
            "title": video_path.stem.replace("_", " ").title(),
            "summary": "User uploaded vertical video.",
            "hook": "",
            "instagram_caption": "",
            "youtube_title": "",
            "youtube_description": "",
            "hashtags": ["#Reels", "#Shorts", "#Viral", "#Explore"],
            "detected_audio": "",
            "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "ready"
        }

        # 2. Multimodal AI Analysis with Gemini
        if GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY, http_options=dict(api_version="v1beta"))
                analysis_data = None

                instruction_text = (
                    f"Additional User Direction: {custom_instruction}\n" if custom_instruction else ""
                )

                system_prompt = f"""You are an elite viral social media director specializing in Instagram Reels and YouTube Shorts.
Carefully inspect this video (both visual actions and any spoken audio or text on screen).
{instruction_text}

Provide an in-depth, authentic analysis and generate optimized publishing metadata:
1. 'summary': 2-3 sentences accurately describing what happens in the video (characters/subjects, actions, setting).
2. 'detected_audio': Summary of spoken narration, dialogue, or audio track.
3. 'title': A compelling, high-converting title (under 50 characters, 4-6 words).
4. 'hook': A scroll-stopping opening hook line to capture instant attention.
5. 'instagram_caption': An engaging, full Instagram caption formatted with emojis, narrative line breaks, a natural call to action (like 'Double tap if...', 'Save this for later', etc.), and a hashtag block at the end.
6. 'hashtags': An array of 15-20 targeted, relevant trending and niche hashtags (e.g. ['#ViralReel', '#Shorts', ...]).
7. 'youtube_title': YouTube Shorts title ending with #Shorts (under 100 characters).
8. 'youtube_description': SEO-friendly description for YouTube Shorts including summary and keywords.

Return ONLY a valid JSON object matching these exact keys."""

                # Attempt Native Video Upload via Gemini File API
                # (For videos under 100MB, File API gives perfect visual + audio comprehension)
                file_size_mb = video_path.stat().st_size / (1024 * 1024)
                if file_size_mb <= 80:
                    try:
                        print("   📡 Uploading video to Gemini for native audiovisual analysis...")
                        gemini_file = client.files.upload(file=str(video_path))
                        # Wait for file processing state
                        max_wait = 15
                        while max_wait > 0 and gemini_file.state.name == "PROCESSING":
                            time.sleep(1)
                            max_wait -= 1
                            gemini_file = client.files.get(name=gemini_file.name)

                        if gemini_file.state.name == "ACTIVE":
                            print("   🧠 Gemini watching and listening to video...")
                            resp = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[gemini_file, system_prompt]
                            )
                            analysis_data = _extract_json(resp.text)
                    except Exception as upload_err:
                        print(f"   ⚠️ File API upload fallback ({upload_err}). Switching to keyframe analysis...")

                # Keyframe Fallback if File API was skipped or failed
                if not analysis_data:
                    print("   🎞️ Extracting video keyframes for visual analysis...")
                    frames = cls.extract_keyframes(video_path, count=6)
                    if frames:
                        pil_images = [Image.open(f) for f in frames]
                        print("   🧠 Analyzing visual keyframes with Gemini 2.5 Flash...")
                        resp = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[*pil_images, system_prompt]
                        )
                        analysis_data = _extract_json(resp.text)

                if analysis_data:
                    metadata["title"] = analysis_data.get("title") or metadata["title"]
                    metadata["summary"] = analysis_data.get("summary") or metadata["summary"]
                    metadata["hook"] = analysis_data.get("hook") or metadata["hook"]
                    metadata["detected_audio"] = analysis_data.get("detected_audio") or ""
                    metadata["instagram_caption"] = analysis_data.get("instagram_caption") or ""
                    metadata["youtube_title"] = analysis_data.get("youtube_title") or f"{metadata['title']} #Shorts"
                    metadata["youtube_description"] = analysis_data.get("youtube_description") or metadata["summary"]
                    if analysis_data.get("hashtags"):
                        metadata["hashtags"] = analysis_data["hashtags"]
                    print(f"   ✅ AI Analysis complete! Title: '{metadata['title']}'")
            except Exception as e:
                print(f"   ⚠️ Gemini analysis failed ({e}). Using default heuristic metadata.")

        # If caption wasn't generated by AI, create a high-quality default
        if not metadata["instagram_caption"]:
            tag_str = " ".join(metadata["hashtags"])
            metadata["instagram_caption"] = (
                f"{metadata['title']}\n\n"
                f"{metadata['summary']}\n\n"
                "Double tap if you enjoyed this! ❤️ Save for later and share with friends ✨\n\n"
                f".\n.\n{tag_str}"
            )

        if not metadata["youtube_title"]:
            clean_title = metadata["title"][:90]
            metadata["youtube_title"] = f"{clean_title} #Shorts"

        if not metadata["youtube_description"]:
            metadata["youtube_description"] = f"{metadata['title']}\n\n{metadata['summary']}\n\n#Shorts #Reels #Viral"

        # 3. Write Companion JSON File
        companion_json = video_path.parent / f"{video_path.stem}.json"
        try:
            with open(companion_json, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"   📄 Companion metadata saved to {companion_json.name}")
        except Exception as e:
            print(f"   ⚠️ Failed to save companion json: {e}")

        return metadata

    @classmethod
    def get_video_metadata(cls, video_path: Path) -> Dict[str, Any]:
        """Returns existing companion metadata or generates fresh analysis."""
        video_path = Path(video_path).resolve()
        companion_json = video_path.parent / f"{video_path.stem}.json"

        if companion_json.exists():
            try:
                with open(companion_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure thumbnail path is valid
                    thumb_file = video_path.parent / f"{video_path.stem}_thumb.jpg"
                    if thumb_file.exists():
                        folder_name = "published" if "published" in str(video_path) else "output"
                        data["thumbnail"] = f"/media/{folder_name}/{thumb_file.name}"
                    return data
            except Exception:
                pass

        return cls.analyze_video(video_path)
