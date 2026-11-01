import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

DEFAULT_HASHTAGS = [
    "#reels", "#viral", "#didyouknow", "#facts", "#mindblown", 
    "#science", "#psychology", "#technology", "#curiosity", "#shorts"
]

NICHE_HASHTAGS = {
    "psychology": ["#psychology", "#darkpsychology", "#mindhacks", "#humanbehavior", "#brainfacts"],
    "wealth": ["#wealth", "#money", "#billionairemindset", "#financialfreedom", "#success"],
    "history": ["#history", "#ancienthistory", "#untoldhistory", "#historicalfacts", "#ancientsecrets"],
    "space": ["#space", "#astronomy", "#cosmos", "#universe", "#nasa", "#blackhole"],
    "tech": ["#tech", "#futuretech", "#artificialintelligence", "#ai", "#innovation"],
    "biohack": ["#biohacking", "#longevity", "#healthhacks", "#dopamine", "#fitness"],
    "nature": ["#nature", "#wildlife", "#animals", "#ocean", "#earth"]
}

class MetadataLinker:
    """
    Pairs video files with corresponding Instagram caption, hashtags,
    and cover configurations. Generates viral metadata when missing.
    """

    @staticmethod
    def detect_niche(text: str) -> List[str]:
        lower = text.lower()
        matched_tags = []
        for niche, tags in NICHE_HASHTAGS.items():
            if niche in lower:
                matched_tags.extend(tags)
        if not matched_tags:
            for niche, tags in NICHE_HASHTAGS.items():
                if any(k in lower for k in [niche[:4], "mind", "fact", "secret", "why"]):
                    matched_tags.extend(tags)
                    break
        return matched_tags if matched_tags else DEFAULT_HASHTAGS[:5]

    @staticmethod
    def generate_caption_from_title(title: str) -> str:
        """
        Creates an engaging, viral-optimized Instagram caption with hook,
        clean spacing, call to action, and hashtags.
        """
        clean_title = title.replace("_", " ").strip()
        tags = MetadataLinker.detect_niche(clean_title)
        tags_str = " ".join(tags + ["#reels", "#fyp", "#explorepage"])

        caption = (
            f"🤯 {clean_title}\n\n"
            f"Did you know this? Drop your thoughts below! 👇\n\n"
            f"🔔 Follow for daily mind-opening revelations and untold facts.\n"
            f"📲 Share this with someone who needs to see this!\n\n"
            f"{tags_str}"
        )
        return caption

    @staticmethod
    def extract_cover_thumbnail(video_path: Path, output_thumbnail: Path, timestamp: float = 1.0) -> Optional[Path]:
        """
        Extracts a high-quality JPEG cover thumbnail from the video at the given timestamp.
        """
        try:
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_thumbnail)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return output_thumbnail if output_thumbnail.exists() else None
        except Exception:
            return None

    @staticmethod
    def link_metadata(video_path: Path) -> Dict[str, Any]:
        """
        Finds or constructs metadata for the given video file.
        Lookup priority:
        1. {stem}.json (Full structured config)
        2. {stem}.txt (Raw caption text)
        3. Dynamic auto-generation from filename
        """
        video_path = Path(video_path).resolve()
        stem = video_path.stem
        parent = video_path.parent

        json_meta_path = parent / f"{stem}.json"
        txt_meta_path = parent / f"{stem}.txt"

        caption = ""
        share_to_feed = True
        thumb_offset_ms = 1000
        cover_image_path: Optional[str] = None
        custom_fields: Dict[str, Any] = {}

        # 1. JSON Configuration
        if json_meta_path.exists():
            try:
                with open(json_meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                caption = data.get("caption", "")
                if not caption and "title" in data:
                    caption = MetadataLinker.generate_caption_from_title(data["title"])
                share_to_feed = data.get("share_to_feed", True)
                thumb_offset_ms = data.get("thumb_offset_ms", 1000)
                cover_image_path = data.get("cover_image", None)
                custom_fields = data
            except Exception as e:
                print(f"[MetadataLinker Warning] Failed to parse {json_meta_path.name}: {e}")

        # 2. Text File Configuration
        if not caption and txt_meta_path.exists():
            try:
                with open(txt_meta_path, "r", encoding="utf-8") as f:
                    caption = f.read().strip()
            except Exception as e:
                print(f"[MetadataLinker Warning] Failed to read {txt_meta_path.name}: {e}")

        # 3. Auto-generation fallback
        if not caption:
            caption = MetadataLinker.generate_caption_from_title(stem)

        # 4. Check for companion cover image (jpg or png)
        if not cover_image_path:
            for ext in [".jpg", ".jpeg", ".png"]:
                candidate = parent / f"{stem}{ext}"
                if candidate.exists():
                    cover_image_path = str(candidate)
                    break

        metadata = {
            "video_path": str(video_path),
            "stem": stem,
            "caption": caption,
            "share_to_feed": share_to_feed,
            "thumb_offset_ms": thumb_offset_ms,
            "cover_image": cover_image_path,
            "custom": custom_fields
        }

        return metadata

