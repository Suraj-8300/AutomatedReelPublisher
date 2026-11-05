#!/usr/bin/env python3
"""
AutoReelStudio — Unified Autonomous AI Video Generation & Meta Reels Publishing CLI
Integrates:
  - ReelMakerAI: Autonomous AI video storyboarding, voiceover, music, subtitles, and rendering
  - ReelPublisher: Direct Meta Graph API publisher, resumable ingestion, queue manager, and QC
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.creative_randomizer import GENRE_TAXONOMY, GENERATION_MODES
from core.genre_catalog import get_catalog_topics
from core.cache_manager import CacheManager

BANNER = r"""
   ___        __        ___          _ ___ _           _ _     
  / _ \      / /_____  / _ \___ ___ / / __/ |_ _  _ __| (_)___ 
 / /_\ \    / // _ \ \/ // -_) -_) // _\ |  _| || / _` | / _ \
/_/   \_\  /_/ \___/\__/\__/\__/\___/|___/\__|\_,_\__,_|_\___/
      Autonomous AI Video Generator (ReelMakerAI)
           & Meta Reels Publisher (ReelPublisher)
"""

def print_banner():
    print(BANNER)

def cmd_make(args):
    """Generates an intelligent Instagram Reel via ReelMakerAI pipeline."""
    from generate import run_pipeline, send_to_instagram_inbox

    output_video, storyboard, qc_result = asyncio.run(run_pipeline(
        prompt=args.prompt,
        duration=args.duration,
        genre=args.genre,
        subgenre=args.subgenre,
        mode=args.mode,
        voice=args.voice,
        music_style=args.music,
        caption_style=args.caption_style,
        theme=args.theme,
        seed=args.seed,
        run_qc=not args.no_qc,
        animal_species=args.animal,
        visual_style=args.style,
        activity_type=args.activity,
        is_duo=args.duo
    ))

    if args.to_inbox or args.publish:
        send_to_instagram_inbox(
            output_mp4=output_video,
            storyboard=storyboard,
            auto_publish=args.publish,
            dry_run=args.dry_run
        )
    return output_video

def cmd_publish(args):
    """Processes and publishes a video file to Instagram Reels via ReelPublisher pipeline."""
    from reel_publisher import cmd_process
    cmd_process(args)

def cmd_studio(args):
    """Launches the AutoReelStudio Web Interface."""
    from server import start_server
    port = args.port or int(os.environ.get("PORT", 8080))
    start_server(port=port)

def cmd_auto(args):
    """Autonomous generation and publication to Instagram Reels and/or YouTube Shorts."""
    from generate import run_pipeline, send_to_instagram_inbox

    print("🚀 [AutoReelStudio] Initiating Autonomous Generate & Publish Pipeline...")
    output_video, storyboard, qc_result = asyncio.run(run_pipeline(
        prompt=args.prompt,
        duration=args.duration,
        genre=args.genre,
        mode=args.mode,
        caption_style=args.caption_style,
        animal_species=args.animal,
        visual_style=args.style,
        activity_type=args.activity,
        is_duo=args.duo,
        run_qc=True
    ))

    dest = getattr(args, "target", "instagram")

    # 1. Instagram Reels Publishing
    if dest in ["instagram", "both", "all"]:
        print(f"\n📤 [AutoReelStudio] Dispatching rendered video to Instagram Reels...")
        send_to_instagram_inbox(
            output_mp4=output_video,
            storyboard=storyboard,
            auto_publish=True,
            dry_run=args.dry_run
        )

    # 2. YouTube Shorts Publishing
    if dest in ["youtube", "both", "all"]:
        from youtube_pipeline.auth import YouTubeAuthenticator
        from youtube_pipeline.publisher import YouTubePublisher
        if not YouTubeAuthenticator.is_authenticated():
            print("⚠️ [YouTube] YouTube channel not authorized. Run 'python3 autoreel.py auth-youtube' first.")
        else:
            print(f"\n📤 [AutoReelStudio] Uploading rendered video to YouTube Shorts...")
            pub = YouTubePublisher()
            title = storyboard.get("title", "Autonomous AI Reel")
            script = storyboard.get("script", "")
            pub.upload_short(
                video_path=Path(output_video),
                title=title,
                description=script,
                privacy_status="public" if not args.dry_run else "private"
            )

def cmd_auth_youtube(args):
    """Starts local server to complete OAuth 2.0 authorization for YouTube."""
    from youtube_pipeline.auth import YouTubeAuthenticator
    YouTubeAuthenticator.run_local_auth_server(timeout_secs=args.timeout)

def cmd_publish_youtube(args):
    """Publishes a video file directly to YouTube Shorts."""
    from youtube_pipeline.publisher import YouTubePublisher
    title = args.title or Path(args.video).stem.replace("_", " ")
    pub = YouTubePublisher()
    pub.upload_short(
        video_path=Path(args.video),
        title=title,
        description=args.desc or "",
        privacy_status=args.privacy
    )

def cmd_check(args):
    """Audits video against Instagram Reels technical specs."""
    from reel_publisher import cmd_check as check_fn
    check_fn(args)

def cmd_watch(args):
    """Watches reels_inbox/ and publishes incoming videos."""
    from reel_publisher import cmd_watch as watch_fn
    watch_fn(args)

def cmd_clean(args):
    """Cleans temporary cache files and reports storage telemetry."""
    print("🧹 [AutoReelStudio] Running Cache Garbage Collection...")
    res = CacheManager.purge_all(keep_stock_clips=2)
    stats = CacheManager.get_cache_stats()
    print(f"  • Files removed:   {res['deleted_count']}")
    print(f"  • Storage freed:   {res['freed_mb']} MB")
    print(f"  • Current cache:   {stats['total_mb']} MB ({stats['file_count']} files)")

def cmd_topics(args):
    """Lists pre-built catalog topics across genres."""
    print("\n📚 Available AutoReelStudio Catalog Topics:")
    for t in get_catalog_topics():
        print(f"  • [{t['genre'].upper():12s}] {t['title']} ({t.get('subgenre', '')})")

def main():
    parser = argparse.ArgumentParser(
        prog="autoreel",
        description="AutoReelStudio: Unified Autonomous AI Video Generator (ReelMakerAI) & Meta Reels Publisher (ReelPublisher)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="AutoReelStudio Subcommands")

    # Command: make (ReelMakerAI)
    p_make = subparsers.add_parser("make", aliases=["generate", "create"], help="Generate fresh Reel (ReelMakerAI engine)")
    p_make.add_argument("-p", "--prompt", default=None, help="Custom prompt / concept (or leave empty for autonomous engine)")
    p_make.add_argument("-d", "--duration", type=int, choices=[10, 15, 30, 60], default=15, help="Video duration in seconds")
    p_make.add_argument("-g", "--genre", default=None, choices=list(GENRE_TAXONOMY.keys()), help="Creative genre")
    p_make.add_argument("--subgenre", default=None, help="Specific subgenre within selected genre")
    p_make.add_argument("-m", "--mode", default="balanced", choices=list(GENERATION_MODES.keys()), help="Creative mode")
    p_make.add_argument("-c", "--caption-style", default=None, choices=["karaoke", "high_impact", "clean_minimal", "cinematic", "dynamic_phrase", "meme"], help="Subtitle typography")
    p_make.add_argument("-v", "--voice", default=None, help="Voice actor")
    p_make.add_argument("--music", default=None, help="Soundtrack style")
    p_make.add_argument("-t", "--theme", default=None, help="Color theme")
    p_make.add_argument("--seed", type=int, default=None, help="Deterministic seed")
    p_make.add_argument("--no-qc", action="store_true", help="Skip quality control check")
    p_make.add_argument("--to-inbox", action="store_true", help="Queue into Instagram Reels inbox")
    p_make.add_argument("--publish", action="store_true", help="Publish directly to Instagram Reels")
    p_make.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing in dry-run mode")
    p_make.add_argument("--animal", default=None, help="Animal species for Animal Storytelling mode")
    p_make.add_argument("--style", default=None, choices=["photorealistic", "pixar_3d", "cartoon_2d", "anime", "stop_motion", "fantasy_world"], help="Visual style")
    p_make.add_argument("--activity", default=None, help="Human-like animal activity")
    p_make.add_argument("--duo", action="store_true", help="Generate an unusual animal duo story")

    # Command: publish (ReelPublisher)
    p_pub = subparsers.add_parser("publish", aliases=["post"], help="Publish video to Instagram Reels (ReelPublisher engine)")
    p_pub.add_argument("video", help="Path to input MP4 video file")
    p_pub.add_argument("--mode", choices=["pad", "crop", "blur_pad"], default="pad", help="Aspect scaling mode")
    p_pub.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing in dry-run mode")

    # Command: studio (Web UI)
    p_studio = subparsers.add_parser("studio", aliases=["web", "serve", "ui"], help="Start AutoReelStudio Web Dashboard")
    p_studio.add_argument("--port", type=int, default=8080, help="Port to run web server on (default: 8080)")

    # Command: auto (1-Click Generate + Live Publish)
    p_auto = subparsers.add_parser("auto", help="1-Click autonomous generation and direct publishing")
    p_auto.add_argument("-p", "--prompt", default=None, help="Custom prompt or leave empty for creative engine")
    p_auto.add_argument("-d", "--duration", type=int, choices=[10, 15, 30, 60], default=15, help="Video duration in seconds")
    p_auto.add_argument("-g", "--genre", default=None, choices=list(GENRE_TAXONOMY.keys()), help="Creative genre")
    p_auto.add_argument("-m", "--mode", default="balanced", choices=list(GENERATION_MODES.keys()), help="Creative mode")
    p_auto.add_argument("-c", "--caption-style", default=None, choices=["karaoke", "high_impact", "clean_minimal", "cinematic", "dynamic_phrase", "meme"], help="Subtitle typography")
    p_auto.add_argument("--animal", default=None, help="Animal species")
    p_auto.add_argument("--style", default=None, choices=["photorealistic", "pixar_3d", "cartoon_2d", "anime", "stop_motion", "fantasy_world"], help="Visual style")
    p_auto.add_argument("--activity", default=None, help="Human-like animal activity")
    p_auto.add_argument("--duo", action="store_true", help="Generate animal duo story")
    p_auto.add_argument("--target", default="instagram", choices=["instagram", "youtube", "both", "all"], help="Destination platform: instagram, youtube, or both")
    p_auto.add_argument("--dry-run", action="store_true", help="Simulate publishing in dry-run mode")

    # Command: auth-youtube (OAuth 2.0 Flow)
    p_auth_yt = subparsers.add_parser("auth-youtube", help="Authorize YouTube channel via Google OAuth 2.0 (port 8000)")
    p_auth_yt.add_argument("--timeout", type=int, default=180, help="Authorization timeout in seconds (default: 180)")

    # Command: publish-youtube (Direct Shorts Upload)
    p_pub_yt = subparsers.add_parser("publish-youtube", help="Publish a video file to YouTube Shorts")
    p_pub_yt.add_argument("video", help="Path to input MP4 video file")
    p_pub_yt.add_argument("--title", default=None, help="Shorts title")
    p_pub_yt.add_argument("--desc", default=None, help="Shorts description")
    p_pub_yt.add_argument("--privacy", default="public", choices=["public", "private", "unlisted"], help="Video privacy")

    # Command: check (QC / Compliance)
    p_check = subparsers.add_parser("check", aliases=["audit", "inspect"], help="Check video compliance against Instagram Reels specifications")
    p_check.add_argument("video", help="Path to video file")

    # Command: watch (Folder Ingestion Daemon)
    p_watch = subparsers.add_parser("watch", help="Watch reels_inbox/ for incoming footage and auto-publish")
    p_watch.add_argument("--interval", type=float, default=5.0, help="Poll interval in seconds")
    p_watch.add_argument("--mode", choices=["pad", "crop", "blur_pad"], default="pad", help="Scaling mode")
    p_watch.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing")

    # Command: clean (Storage & Cache GC)
    subparsers.add_parser("clean", help="Clean render cache and temp clips")

    # Command: topics (Catalog topics)
    subparsers.add_parser("topics", aliases=["catalog"], help="List pre-built catalog topics across genres")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command in ["make", "generate", "create"]:
        cmd_make(args)
    elif args.command in ["publish", "post"]:
        cmd_publish(args)
    elif args.command in ["studio", "web", "serve", "ui"]:
        cmd_studio(args)
    elif args.command == "auto":
        cmd_auto(args)
    elif args.command == "auth-youtube":
        cmd_auth_youtube(args)
    elif args.command == "publish-youtube":
        cmd_publish_youtube(args)
    elif args.command in ["check", "audit", "inspect"]:
        cmd_check(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command in ["topics", "catalog"]:
        cmd_topics(args)

if __name__ == "__main__":
    main()
