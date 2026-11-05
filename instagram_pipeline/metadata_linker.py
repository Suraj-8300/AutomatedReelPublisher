import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

GENRE_HASHTAGS = {
    "comedy": ["#comedyreels", "#funnyreels", "#relatablehumor", "#relatable", "#comedy"],
    "meme": ["#memes", "#pov", "#relatablememes", "#trendingreels", "#funnymemes"],
    "science": ["#sciencefacts", "#astronomy", "#physics", "#sciencereels", "#stem"],
    "mysteries": ["#mysteries", "#ancienthistory", "#oceanmysteries", "#unsolved", "#history"],
    "informative": ["#deepthoughts", "#criticalthinking", "#knowledge", "#mindset", "#insight"],
    "emotional": ["#inspiration", "#lifelessons", "#motivation", "#storytelling", "#perseverance"],
    "storytelling": ["#shortstory", "#scifi", "#suspense", "#storyteller", "#reelsstory"],
    "animation": ["#animation", "#cartoon", "#animators", "#2danimation", "#animatedshort"],
    "cinematic": ["#cinematic", "#filmmaking", "#cinematography", "#action", "#moody"]
}

GENRE_CTAS = {
    "comedy": [
        "Has this ever happened to you? Tell me below 😂",
        "Tag the friend who does this every single time 👇",
        "Be honest: are you guilty of this too?",
        "Drop your worst shopping or coffee story below 👇"
    ],
    "meme": [
        "Tell me I am not the only one who does this 💀",
        "Tag someone who needs to see this right now 👇",
        "What is your go-to move when this happens?",
        "Send this to your group chat without context 😭"
    ],
    "science": [
        "What part of this surprised you the most?",
        "Save this for your next late-night cosmic rabbit hole 🌌",
        "Did you already know about this mechanism?",
        "Drop your favorite science fact in the comments 👇"
    ],
    "mysteries": [
        "What is your theory on what really happened here?",
        "Save this to explore the archives later 📜",
        "Which ancient mystery should we investigate next?",
        "Would you explore these depths yourself?"
    ],
    "informative": [
        "How do you approach this in your own life?",
        "Save this post to revisit when making tough decisions 💡",
        "What is your take on this perspective?",
        "Share this with someone who appreciates critical thinking."
    ],
    "emotional": [
        "What is one quiet victory you are proud of recently?",
        "Send this to someone who needed a reminder today ❤️",
        "Never underestimate the compounding power of small courage.",
        "Take a second today to appreciate the people in your corner."
    ],
    "storytelling": [
        "Did you see that ending coming?",
        "What would you have done in this situation?",
        "Save this story for later 📖",
        "Part two coming soon. What do you think happens next?"
    ],
    "animation": [
        "Who won this battle: Brain or Snooze? 😂",
        "Which animated character should we animate next?",
        "Drop a comment if you felt this in your soul 👾"
    ],
    "cinematic": [
        "Headphones on for this one 🎧",
        "Which cinematic scene hits you like this?",
        "Save this for pre-workout or focus motivation 🔥"
    ]
}

class MetadataLinker:
    """
    Intelligent Instagram Post Metadata & Companion Caption Engine.
    Produces authentic, genre-tailored captions with selective hashtags,
    natural discussion hooks, and zero spammy filler.
    """

    @staticmethod
    def generate_caption(
        title: str,
        genre: str = "science",
        hook: Optional[str] = None,
        source: Optional[str] = None
    ) -> str:
        """
        Creates a clean, engaging Instagram caption tailored to the genre.
        """
        import random
        clean_title = title.replace("_", " ").strip()
        tags = GENRE_HASHTAGS.get(genre, GENRE_HASHTAGS["science"])
        tags_str = " ".join(tags[:5] + ["#reels"])

        ctas = GENRE_CTAS.get(genre, GENRE_CTAS["science"])
        selected_cta = random.choice(ctas)

        # Hook / lead line
        lead_line = hook if hook else f"The reality of {clean_title}."

        caption_parts = [
            f"{lead_line}\n",
            f"{selected_cta}\n"
        ]

        # Add verified source credit for science or history
        if source and source not in ["Original Generation", "Custom User Topic"]:
            caption_parts.append(f"📌 Source: {source}\n")

        caption_parts.append(tags_str)

        return "\n".join(caption_parts)

    @staticmethod
    def generate_caption_from_title(title: str) -> str:
        """Fallback helper maintaining backward compatibility."""
        return MetadataLinker.generate_caption(title=title, genre="science")

    @staticmethod
    def extract_cover_thumbnail(video_path: Path, output_thumbnail: Path, timestamp: float = 1.0) -> Optional[Path]:
        """Extracts cover thumbnail from video container."""
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
        """Finds or constructs metadata for the given video file."""
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

        if json_meta_path.exists():
            try:
                with open(json_meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                caption = data.get("caption", "")
                if not caption and "title" in data:
                    caption = MetadataLinker.generate_caption(
                        title=data.get("title", stem),
                        genre=data.get("genre", "science"),
                        hook=data.get("hook"),
                        source=data.get("source")
                    )
                share_to_feed = data.get("share_to_feed", True)
                thumb_offset_ms = data.get("thumb_offset_ms", 1000)
                cover_image_path = data.get("cover_image", None)
                custom_fields = data
            except Exception as e:
                print(f"[MetadataLinker Warning] Failed to parse {json_meta_path.name}: {e}")

        if not caption and txt_meta_path.exists():
            try:
                with open(txt_meta_path, "r", encoding="utf-8") as f:
                    caption = f.read().strip()
            except Exception as e:
                print(f"[MetadataLinker Warning] Failed to read {txt_meta_path.name}: {e}")

        if not caption:
            caption = MetadataLinker.generate_caption(title=stem)

        if not cover_image_path:
            for ext in [".jpg", ".jpeg", ".png"]:
                candidate = parent / f"{stem}{ext}"
                if candidate.exists():
                    cover_image_path = str(candidate)
                    break

        return {
            "video_path": str(video_path),
            "stem": stem,
            "caption": caption,
            "share_to_feed": share_to_feed,
            "thumb_offset_ms": thumb_offset_ms,
            "cover_image": cover_image_path,
            "custom": custom_fields
        }
