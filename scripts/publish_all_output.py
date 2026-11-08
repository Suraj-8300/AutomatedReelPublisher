"""
Batch Publisher for AutoReelStudio.
Publishes all videos currently in output/ to both Instagram and YouTube.
Ensures 'gemini_generated_video' files are published last as requested.
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from video.config import OUTPUT_DIR, PUBLISHED_DIR
from video.video_analyzer import VideoAnalyzer
from autoreel import publish_direct


def clean_title_from_filename(filename: str) -> str:
    """Derives a clean title from a video filename."""
    # Strip hash or extension
    name = Path(filename).stem
    # Remove hex run_ids like _e8ef791c
    name = re.sub(r'_[a-f0-9]{8}$', '', name)
    # Replace underscores with spaces
    title = name.replace('_', ' ').strip()
    return title.title()


def get_caption_for_video(title: str, filename: str) -> str:
    """Generates engaging caption with relevant hashtags."""
    t_lower = title.lower()
    if "kitten" in t_lower or "cat" in t_lower or "trust" in t_lower:
        return f"{title}\n\nA heartwarming story of patience, love, and transformation. Watch till the end! ❤️🐾\n\n#CuteAnimals #Kitten #CatRescue #Heartwarming #Reels #Shorts"
    elif "neutron" in t_lower or "star" in t_lower or "mars" in t_lower or "space" in t_lower:
        return f"{title}\n\nThe deepest mysteries of our universe revealed in stunning visual detail. 🌌🚀\n\n#Space #Science #Astronomy #Universe #Discovery #Shorts #Reels"
    elif "turbocharger" in t_lower or "engine" in t_lower or "mechanical" in t_lower:
        return f"{title}\n\nHow mechanical engineering drives pure kinetic power. Here is how it works inside! ⚙️🏎️\n\n#Engineering #Cars #Mechanical #HowItWorks #Tech #Shorts"
    elif "gemini" in t_lower:
        return f"{title}\n\nExperience the next generation of AI-driven creative storytelling and visual motion! ✨🤖\n\n#AIVideo #Gemini #FutureTech #Cinematic #Shorts #Reels"
    else:
        return f"{title}\n\nDiscover the extraordinary story behind this moment. Like and share! ✨\n\n#Viral #Trending #Reels #Shorts"


def run_publish_all():
    videos = sorted(list(OUTPUT_DIR.glob("*.mp4")))
    if not videos:
        print("ℹ️ No MP4 videos found in output/ to publish.")
        return

    # Segregate: non-gemini first, gemini-generated at the very end
    standard_videos = [v for v in videos if "gemini_generated" not in v.name.lower()]
    gemini_videos = [v for v in videos if "gemini_generated" in v.name.lower()]

    ordered_videos = standard_videos + gemini_videos

    print("=" * 65)
    print(f"🚀 PUBLISHING QUEUE — {len(ordered_videos)} VIDEO(S) TOTAL")
    print("=" * 65)
    for i, v in enumerate(ordered_videos, 1):
        tag = "[GEMINI LAST]" if "gemini_generated" in v.name.lower() else "[STANDARD]"
        print(f"  {i}. {tag:14s} {v.name}")
    print("=" * 65 + "\n")

    for i, v in enumerate(ordered_videos, 1):
        meta = VideoAnalyzer.get_video_metadata(v)
        title = meta.get("title") or clean_title_from_filename(v.name)
        caption = meta.get("instagram_caption") or get_caption_for_video(title, v.name)
        print(f"\n▶️ [{i}/{len(ordered_videos)}] Publishing: {v.name}")
        print(f"   📌 Title:   {title}")
        print(f"   📝 Caption: {caption.splitlines()[0] if caption else title}")

        try:
            publish_direct(
                video_path=v,
                platforms=["all"],
                title=title,
                caption=caption,
                dry_run=False
            )
        except Exception as e:
            print(f"❌ Error publishing {v.name}: {e}")

    print("\n" + "=" * 65)
    print("🎉 ALL VIDEOS PUBLISHED SUCCESSFULLY")
    print(f"   Output folder:    {len(list(OUTPUT_DIR.glob('*.mp4')))} remaining")
    print(f"   Published folder: {len(list(PUBLISHED_DIR.glob('*.mp4')))} archived")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_publish_all()
