#!/usr/bin/env python3
"""
AutoReel CLI — Clean, Direct Publishing for Instagram Reels & YouTube Shorts.
Direct publishing with zero automation, zero queues, and zero background services.
"""

import os
import sys
from pathlib import Path

# Auto-switch into project virtual environment if executed with system python
PROJECT_ROOT = Path(__file__).resolve().parent
_venv_dir = PROJECT_ROOT / ".venv" if (PROJECT_ROOT / ".venv").exists() else PROJECT_ROOT / "venv"
_venv_python = _venv_dir / "bin" / "python3"
if _venv_python.exists() and sys.prefix != str(_venv_dir):
    if os.environ.get("_AUTOREEL_VENV_ACTIVE") != "1":
        os.environ["_AUTOREEL_VENV_ACTIVE"] = "1"
        try:
            os.execv(str(_venv_python), [str(_venv_python)] + sys.argv)
        except Exception:
            pass

import argparse
import shutil
import datetime
from typing import Optional, List

# Ensure PROJECT_ROOT is in sys.path
sys.path.insert(0, str(PROJECT_ROOT))

from youtube.auth import YouTubeAuthenticator
from youtube.publisher import YouTubePublisher
from youtube.config import get_client_secret_file, get_token_file
from instagram.publisher import MetaGraphPublisher
from instagram.preprocessor import VideoPreprocessor
from instagram.cloud_bridge import CloudBridge
from instagram.config import (
    INSTAGRAM_ACCOUNT_ID,
    META_ACCESS_TOKEN
)
from video import CDNOptimizer, ReelGenerator, BatchGenerator
from video.sources import WikipediaFeed, TopicRotator


def check_auth_status():
    """Audits YouTube OAuth tokens and Instagram Meta Graph API credentials."""
    print("\n" + "=" * 65)
    print("🔐 CREDENTIALS & AUTHENTICATION AUDIT")
    print("=" * 65)

    # 1. Instagram Meta Graph API
    print("\n📸 [INSTAGRAM REELS (Meta Graph API)]")
    if INSTAGRAM_ACCOUNT_ID and META_ACCESS_TOKEN:
        masked_token = META_ACCESS_TOKEN[:6] + "..." + META_ACCESS_TOKEN[-4:]
        print(f"  ✅ Account ID:    {INSTAGRAM_ACCOUNT_ID}")
        print(f"  ✅ Access Token:  {masked_token} (Loaded from .env / instagram.env)")
        print(f"  ⚡ Status:        CONFIGURED & READY")
    else:
        print(f"  ❌ Missing credentials in .env or instagram/instagram.env")
        if not INSTAGRAM_ACCOUNT_ID:
            print("     - INSTAGRAM_ACCOUNT_ID is unset")
        if not META_ACCESS_TOKEN:
            print("     - META_ACCESS_TOKEN is unset")

    # 2. YouTube Data API v3
    print("\n▶️ [YOUTUBE SHORTS (Google Data API v3)]")
    token_file = get_token_file()
    client_secret = get_client_secret_file()

    if not client_secret.exists():
        print(f"  ❌ client_secret.json not found in youtube/ or root")
    else:
        print(f"  ✅ client_secret.json present at {client_secret.relative_to(PROJECT_ROOT)}")

    if not token_file.exists():
        print(f"  ⚠️ youtube_token.json not found in youtube/. Run OAuth to connect.")
    else:
        print(f"  ✅ youtube_token.json present at {token_file.relative_to(PROJECT_ROOT)}")
        try:
            yt_service = YouTubeAuthenticator.get_authenticated_service()
            channels_response = yt_service.channels().list(
                mine=True,
                part="snippet,contentDetails,statistics"
            ).execute()
            items = channels_response.get("items", [])
            if items:
                ch = items[0]
                ch_title = ch.get("snippet", {}).get("title", "Unknown")
                ch_id = ch.get("id", "Unknown")
                subscribers = ch.get("statistics", {}).get("subscriberCount", "Hidden")
                print(f"  ✅ Channel Name:  {ch_title}")
                print(f"  ✅ Channel ID:    {ch_id}")
                print(f"  👥 Subscribers:   {subscribers}")
                print(f"  ⚡ Status:        AUTHENTICATED & READY")
            else:
                print(f"  ⚠️ Authenticated, but no YouTube channel found for this Google account.")
        except Exception as e:
            print(f"  ❌ OAuth Token Verification Error: {e}")

    # 3. Output & Published Folders Audit
    from video.config import OUTPUT_DIR, PUBLISHED_DIR
    out_videos = sorted(list(OUTPUT_DIR.glob("*.mp4")))
    pub_videos = sorted(list(PUBLISHED_DIR.glob("*.mp4")))
    print("\n📁 [STORAGE & PUBLISHING STATUS]")
    print(f"  🎬 Output (Ready to Publish): {len(out_videos)} video(s) in {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
    for v in out_videos[:5]:
        print(f"     - {v.name}")
    if len(out_videos) > 5:
        print(f"     ... and {len(out_videos) - 5} more")

    print(f"  📦 Published (Archived):      {len(pub_videos)} video(s) in {PUBLISHED_DIR.relative_to(PROJECT_ROOT)}")
    for v in pub_videos[:5]:
        print(f"     - {v.name}")
    if len(pub_videos) > 5:
        print(f"     ... and {len(pub_videos) - 5} more")

    print("=" * 65 + "\n")


def publish_direct(
    video_path: Path,
    platforms: List[str],
    title: str,
    caption: Optional[str] = None,
    dry_run: bool = False
) -> Path:
    """
    Publishes a video file directly to YouTube and/or Instagram with zero queueing.
    Upon successful publishing, moves the video from output/ to published/ to avoid double-publishing.
    """
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        print(f"❌ Error: Video file does not exist: {video_path}")
        sys.exit(1)

    from video.config import PUBLISHED_DIR
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    if video_path.parent.resolve() == PUBLISHED_DIR.resolve():
        print(f"\n⚠️  WARNING: '{video_path.name}' is already located in published/ directory!")
        print("   This video was previously published. Proceeding with requested upload...\n")

    caption = caption or title
    print("\n" + "=" * 65)
    print("🚀 DIRECT REEL PUBLISHER (NO QUEUE / NO PACING)")
    print("=" * 65)
    print(f"📁 Video:     {video_path.name}")
    print(f"📌 Title:     {title}")
    print(f"📝 Caption:   {caption[:60]}..." if len(caption) > 60 else f"📝 Caption:   {caption}")
    print(f"🎯 Target:    {', '.join(p.upper() for p in platforms)}")
    print(f"🧪 Dry-Run:   {dry_run}")
    print("=" * 65)

    ig_success = False
    yt_success = False
    ig_media_id = None
    yt_url = None

    # 1. Instagram Direct Upload
    if "instagram" in platforms or "all" in platforms:
        print("\n📸 Publishing to Instagram Reels...")
        try:
            ig_pub = MetaGraphPublisher()
            if not ig_pub.is_configured() and not dry_run:
                print("  ❌ Instagram credentials missing in .env")
            else:
                res = ig_pub.publish_pipeline(
                    video_path=video_path,
                    caption=caption,
                    dry_run=dry_run
                )
                if res.get("success"):
                    ig_media_id = res.get("media_id")
                    ig_permalink = res.get("permalink")
                    print(f"  🎉 Published Instagram Reel! Media ID: {ig_media_id}")
                    if ig_permalink:
                        print(f"  🔗 Instagram URL: {ig_permalink}")
                    ig_success = True
        except Exception as e:
            print(f"  ❌ Instagram Publishing Failed: {e}")

    # 2. YouTube Shorts Direct Upload
    if "youtube" in platforms or "all" in platforms:
        print("\n▶️ Publishing to YouTube Shorts...")
        try:
            if dry_run:
                print(f"  ✅ [Dry-Run] YouTube Shorts payload validated.")
                print(f"  🎉 [Dry-Run] YouTube Short publishing simulated successfully.")
                yt_success = True
                yt_url = "https://youtube.com/shorts/dry_run_simulation"
            else:
                yt_pub = YouTubePublisher()
                res = yt_pub.upload_short(
                    video_path=video_path,
                    title=title,
                    description=caption
                )
                if res.get("success"):
                    yt_url = res.get("shorts_url")
                    print(f"  🎉 Published YouTube Short: {yt_url}")
                    yt_success = True
                else:
                    print(f"  ❌ YouTube upload failed: {res.get('error')}")
        except Exception as e:
            print(f"  ❌ YouTube Publishing Failed: {e}")

    # 3. Post-Publishing: Move from output/ to published/ to avoid multiple publish
    target_ig = "instagram" in platforms or "all" in platforms
    target_yt = "youtube" in platforms or "all" in platforms

    overall_success = False
    if target_ig and target_yt:
        overall_success = ig_success or yt_success
    elif target_ig:
        overall_success = ig_success
    elif target_yt:
        overall_success = yt_success

    final_path = video_path

    if dry_run:
        print("\n🧪 [Dry-Run] Video would be moved from output/ to published/ (skipped during simulation).")
    elif overall_success and video_path.exists() and video_path.parent.resolve() != PUBLISHED_DIR.resolve():
        dest_path = PUBLISHED_DIR / video_path.name
        if dest_path.exists():
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = PUBLISHED_DIR / f"{video_path.stem}_{ts}{video_path.suffix}"

        shutil.move(str(video_path), str(dest_path))
        final_path = dest_path

        print("\n" + "=" * 65)
        print("📦 MOVED TO PUBLISHED (AVOIDING MULTIPLE PUBLISH)")
        print("=" * 65)
        print(f"   From: output/{video_path.name}")
        print(f"   To:   published/{dest_path.name}")
        print(f"   🔒 Video is securely archived in published/ and removed from output/.")
        print("=" * 65)

        # Move companion metadata files if any exist (.json, .md)
        for ext in [".json", ".md"]:
            companion = video_path.with_suffix(ext)
            if companion.exists() and companion.parent.resolve() != PUBLISHED_DIR.resolve():
                comp_dest = PUBLISHED_DIR / companion.name
                shutil.move(str(companion), str(comp_dest))
                print(f"   📄 Companion metadata moved: {companion.name} -> published/{comp_dest.name}")

        # Record publication links in history
        history_file = PROJECT_ROOT / "data" / "published_history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if history_file.exists():
            try:
                import json
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        ig_url = ig_permalink if 'ig_permalink' in locals() and ig_permalink else (f"https://www.instagram.com/reel/{ig_media_id}/" if ig_media_id else None)
        entry = {
            "filename": dest_path.name,
            "title": title,
            "caption": caption,
            "published_at": datetime.datetime.now().isoformat(),
            "youtube_url": yt_url,
            "instagram_id": ig_media_id,
            "instagram_url": ig_url,
        }
        history.insert(0, entry)
        import json
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    print("\n✅ Publishing process finished.\n")
    return final_path


def main():
    parser = argparse.ArgumentParser(
        description="AutoReel — Clean, Direct Social Media Reel Publisher"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available Commands")

    # Command: status
    subparsers.add_parser("status", help="Verify Instagram & YouTube credentials and connectivity")

    # Command: publish
    pub_parser = subparsers.add_parser("publish", help="Directly publish an MP4 file immediately")
    pub_parser.add_argument("video_path", type=str, help="Path to local MP4 video file")
    pub_parser.add_argument("--platform", choices=["instagram", "youtube", "all"], default="all",
                            help="Target platform (default: all)")
    pub_parser.add_argument("--title", type=str, default="Viral AI Reel", help="Video title")
    pub_parser.add_argument("--caption", type=str, default="", help="Video caption/description")
    pub_parser.add_argument("--dry-run", action="store_true", help="Simulate upload without actual posting")

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Synthesize a new 9:16 Reel (AI script, voice, visuals & audio)")
    gen_parser.add_argument("--topic", type=str, default=None,
                            help="Topic for the reel (auto-brainstormed via 2-stage Gemini flow if omitted)")
    gen_parser.add_argument("--pillar", choices=["animal_story", "storytelling", "cinematic", "science", "mechanical", "explainer", "ugc_lifestyle", "ugc", "auto"],
                            default="animal_story", help="Content pillar (default: animal_story)")
    gen_parser.add_argument("--publish", action="store_true", help="Automatically publish after generation")
    gen_parser.add_argument("--platform", choices=["instagram", "youtube", "all"], default="all",
                            help="Platform to publish to if --publish is set")
    gen_parser.add_argument("--voice", type=str, default=None, help="Voice style override")
    gen_parser.add_argument("--music", type=str, default=None, help="Music style override")
    gen_parser.add_argument("--visuals", choices=["consistent", "broll", "ai", "auto"], default="auto",
                            help="Visual approach: 'consistent' for character-locked continuity (default), 'broll' for stock video, 'ai' for AI")
    gen_parser.add_argument("--dry-run", action="store_true", help="Simulate upload without actual posting")

    # Command: auto (2-stage Gemini idea generation -> synchronized video)
    auto_parser = subparsers.add_parser("auto", help="Auto-generate a viral reel via 2-stage Gemini flow (prompt -> idea -> video)")
    auto_parser.add_argument("--pillar", choices=["animal_story", "storytelling", "cinematic", "science", "mechanical", "explainer", "ugc_lifestyle", "ugc", "auto"],
                             default="animal_story", help="Content pillar (default: animal_story)")
    auto_parser.add_argument("--publish", action="store_true", help="Automatically publish after generation")
    auto_parser.add_argument("--platform", choices=["instagram", "youtube", "all"], default="all",
                             help="Platform to publish to if --publish is set")
    auto_parser.add_argument("--dry-run", action="store_true", help="Simulate upload without actual posting")

    # Command: ugc (UGC lifestyle & product ad with full production blueprint)
    ugc_parser = subparsers.add_parser("ugc", help="Generate a UGC lifestyle ad & product reel with complete production blueprint")
    ugc_parser.add_argument("--hook", type=str, default="Wait… mango soda actually tastes like this?",
                            help="UGC hook concept (default: 'Wait… mango soda actually tastes like this?')")
    ugc_parser.add_argument("--publish", action="store_true", help="Automatically publish after generation")
    ugc_parser.add_argument("--platform", choices=["instagram", "youtube", "all"], default="all",
                            help="Platform to publish to if --publish is set")
    ugc_parser.add_argument("--dry-run", action="store_true", help="Simulate upload without actual posting")

    # Command: batch
    batch_parser = subparsers.add_parser("batch", help="Generate a full day's batch of 10+ reels")
    batch_parser.add_argument("--count", type=int, default=10, help="Number of reels to generate (default: 10)")
    batch_parser.add_argument("--publish", action="store_true", help="Publish each reel immediately after generation")
    batch_parser.add_argument("--platform", choices=["instagram", "youtube", "all"], default="all",
                              help="Platform to publish to if --publish is set")
    batch_parser.add_argument("--no-wiki", action="store_true", help="Disable Wikipedia feed topic enrichment")

    # Command: publish-all
    pub_all_parser = subparsers.add_parser("publish-all", help="Publish all videos in output/ to YouTube & Instagram (gemini videos published last)")
    pub_all_parser.add_argument("--dry-run", action="store_true", help="Simulate upload without actual posting")

    # Command: serve
    srv_parser = subparsers.add_parser("serve", help="Launch the AutoReelStudio Modern Web Studio UI")
    srv_parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")

    # Command: topics
    subparsers.add_parser("topics", help="Show today's 10-reel schedule and trending topics")

    # Command: optimize
    opt_parser = subparsers.add_parser("optimize", help="Optimize MP4 with faststart moov-atom")
    opt_parser.add_argument("video_path", type=str, help="Path to local MP4 file")
    opt_parser.add_argument("--output", type=str, default=None, help="Output optimized file path")

    # Command: check
    chk_parser = subparsers.add_parser("check", help="Audit video technical compliance")
    chk_parser.add_argument("video_path", type=str, help="Path to local MP4 file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "status":
        check_auth_status()

    elif args.command in ("generate", "auto", "ugc"):
        if args.command == "ugc":
            topic = getattr(args, "hook", "Wait… mango soda actually tastes like this?")
            pillar = "ugc_lifestyle"
        else:
            topic = getattr(args, "topic", None)
            pillar = getattr(args, "pillar", "animal_story")
            pillar = None if pillar == "auto" else pillar

            # If topic is not provided or command is 'auto', trigger 2-stage Gemini flow
            if not topic:
                topic = "auto"

        voice = getattr(args, "voice", None)
        music = getattr(args, "music", None)
        visuals = getattr(args, "visuals", "auto")

        mp4_path, meta = ReelGenerator.generate(
            topic=topic,
            pillar=pillar,
            voice_override=voice,
            music_override=music,
            visuals_override=visuals,
        )

        resolved_topic = meta.get("topic") or topic

        if args.publish and mp4_path and mp4_path.exists():
            platforms = ["instagram", "youtube"] if args.platform == "all" else [args.platform]
            publish_direct(
                video_path=mp4_path,
                platforms=platforms,
                title=resolved_topic,
                caption=meta.get("narration") or resolved_topic,
                dry_run=args.dry_run,
            )

    elif args.command == "batch":
        print(f"🚀 Running batch generation of {args.count} reels...")
        results = BatchGenerator.run_batch(
            count=args.count,
            use_wikipedia=not args.no_wiki,
            auto_publish=args.publish,
            platform=args.platform,
        )

    elif args.command == "publish-all":
        from scripts.publish_all_output import run_publish_all
        run_publish_all()

    elif args.command == "serve":
        from server import run_server
        run_server(port=args.port)

    elif args.command == "topics":
        print("\n" + "=" * 65)
        print("📅 TODAY'S 10-REEL SCHEDULE")
        print("=" * 65)
        schedule = TopicRotator.get_daily_schedule(10)
        for i, (pillar, top) in enumerate(schedule, 1):
            print(f"  {i:2d}. [{pillar.upper():10s}] {top}")

        print("\n📰 TRENDING TOPICS (Wikipedia Live Feed)")
        print("=" * 65)
        try:
            trending = WikipediaFeed.get_trending_topics(limit=8)
            for i, t in enumerate(trending, 1):
                print(f"  {i:2d}. {t['title']} ({t['views']:,} views)")
        except Exception as e:
            print(f"  ⚠️ Could not fetch Wikipedia trending: {e}")
        print("=" * 65 + "\n")

    elif args.command == "publish":
        platforms = ["instagram", "youtube"] if args.platform == "all" else [args.platform]
        publish_direct(
            video_path=Path(args.video_path),
            platforms=platforms,
            title=args.title,
            caption=args.caption or args.title,
            dry_run=args.dry_run
        )

    elif args.command == "optimize":
        vpath = Path(args.video_path)
        out = Path(args.output) if args.output else None
        res = CDNOptimizer.optimize_for_cdn(vpath, output_path=out)
        print(f"✅ Faststart optimization complete: {res}")

    elif args.command == "check":
        vpath = Path(args.video_path)
        meta = VideoPreprocessor.probe_video(vpath)
        res = VideoPreprocessor.validate_compliance(meta)
        print("\nCompliance Audit Results:")
        for k, v in res.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
