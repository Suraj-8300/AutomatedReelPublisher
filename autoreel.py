#!/usr/bin/env python3
"""
AutoReelStudio — Unified Autonomous AI Video Generation & Social Publishing Platform
Modular Architecture:
  1. idea_generation/  -> Research, Ideation, 10-15 Buffer Queue, Feedback Learner
  2. video_generation/ -> AI Visuals, Natural Voice, Ducked Audio, 50/day Quota Gate, Composer
  3. video_processing/ -> CDN Video Optimization (faststart), Metadata Packager (IG + YT)
  4. publishers/       -> Dedicated Platform Publishers (Instagram Meta Graph API + YouTube Data API v3)
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from idea_generation import IdeaQueueManager, IdeaResearchEngine, FeedbackLearner
from video_generation import VideoGenerator, QuotaGovernor, DAILY_MAX_REELS
from video_processing import CDNOptimizer, MetadataPackager
from publishers import InstagramPublisher, InstagramQueueManager, YouTubePublisher, YouTubeAuthenticator

BANNER = r"""
   ___        __        ___          _ ___ _           _ _     
  / _ \      / /_____  / _ \___ ___ / / __/ |_ _  _ __| (_)___ 
 / /_\ \    / // _ \ \/ // -_) -_) // _\ |  _| || / _` | / _ \
/_/   \_\  /_/ \___/\__/\__/\__/\___/|___/\__|\_,_\__,_|_\___/
      Autonomous 4-Stage Multi-Platform Video Studio
       [Ideation -> Generation -> CDN Prep -> Publishing]
"""

def print_banner():
    print(BANNER)

# ==============================================================================
# SUBCOMMAND HANDLERS
# ==============================================================================

def cmd_queue(args):
    """Inspects and manages the 10-15 creative idea buffer queue."""
    if args.action == "replenish":
        res = IdeaQueueManager.replenish_if_needed()
        print(f"💡 [Queue Replenish] {res['message']}")
    elif args.action == "pop":
        idea = IdeaQueueManager.pop_next_idea()
        if idea:
            print(f"🎬 Popped Idea: [{idea.get('genre', '').upper()}] {idea.get('title')}")
            print(f"   Hook: \"{idea.get('hook')}\"")
        else:
            print("⚠️ Queue is currently empty.")
    else:
        # Default: list queue
        queue = IdeaQueueManager.get_queue()
        print("\n" + "=" * 65)
        print(f"📋 AUTOREELSTUDIO IDEA QUEUE ({len(queue)} ideas in buffer)")
        print("   Rule: Buffer maintains 10-15 ideas. If < 10, auto-replenishes.")
        print("=" * 65)
        if not queue:
            print("  (Queue is empty. Run 'python3 autoreel.py queue replenish' to generate 15 ideas)")
        for idx, item in enumerate(queue, 1):
            print(f"  {idx:02d}. [{item.get('genre', 'curiosity').upper():18s}] {item.get('title')}")
            print(f"      Hook: \"{item.get('hook', '')[:65]}...\"")
        print("=" * 65)

def cmd_quota(args):
    """Displays today's 50-reels generation quota telemetry."""
    status = QuotaGovernor.get_status()
    print("\n" + "=" * 65)
    print("📊 DAILY REEL GENERATION QUOTA TELEMETRY")
    print("=" * 65)
    print(f"📅 Date (UTC):       {status['date']}")
    print(f"🎯 Daily Limit:      {status['daily_limit']} Reels (Safety ceiling)")
    print(f"⚡ Generated Today:  {status['generated_today']} Reels")
    print(f"🔋 Remaining Today:  {status['remaining_today']} Reels")
    print(f"📈 Capacity Used:    {status['percent_used']}%")
    print(f"🚦 Status:           {'ALLOWED' if status['allowed'] else 'BLOCKED (Limit Reached)'}")
    print("=" * 65)

def cmd_make(args):
    """Generates an AI video from the idea queue or a custom prompt."""
    if args.prompt:
        idea = IdeaResearchEngine._synthesize_from_custom_prompt(args.prompt, duration=args.duration)
    else:
        idea = IdeaQueueManager.pop_next_idea(auto_replenish=True)
        if not idea:
            print("💡 Queue was empty. Replenishing and selecting fresh idea...")
            IdeaQueueManager.replenish_if_needed()
            idea = IdeaQueueManager.pop_next_idea(auto_replenish=True)

    video_path, telemetry = asyncio.run(VideoGenerator.generate_reel(
        idea=idea,
        voice_override=args.voice,
        music_override=args.music,
        caption_override=args.caption_style
    ))

    # Optional CDN Optimization
    if not args.skip_cdn:
        print("\n⚙️ Running CDN Video Optimization (faststart moov atom, 1080x1920)...")
        cdn_video = CDNOptimizer.optimize_for_cdn(video_path)
        print(f"✅ CDN Optimized Master: {cdn_video.name}")

    return video_path

def cmd_process(args):
    """Runs CDN video processing and formats platform metadata packages."""
    video_path = Path(args.video).resolve()
    print(f"\n🔍 Probing and optimizing: {video_path.name}")
    cdn_video = CDNOptimizer.optimize_for_cdn(video_path)
    specs = CDNOptimizer.probe_video(cdn_video)

    ig_meta = MetadataPackager.package_for_instagram(
        title=video_path.stem.replace("_", " "),
        genre="curiosity",
        hook="Did you know this fascinating truth?"
    )

    yt_meta = MetadataPackager.package_for_youtube(
        title=video_path.stem.replace("_", " "),
        genre="curiosity",
        hook="Did you know this fascinating truth?"
    )

    print("\n" + "=" * 65)
    print("📱 INSTAGRAM METADATA PACKAGE")
    print("=" * 65)
    print(ig_meta["caption"][:180] + "...\n")

    print("=" * 65)
    print("▶️ YOUTUBE SHORTS METADATA PACKAGE")
    print("=" * 65)
    print(f"Title: {yt_meta['title']}")
    print(f"Tags:  {', '.join(yt_meta['tags'][:6])}...")
    print("=" * 65)

def cmd_publish(args):
    """Publishes a video to Instagram Reels or YouTube Shorts."""
    video_path = Path(args.video).resolve()
    platform = args.platform.lower()

    if platform in ["instagram", "ig"]:
        print(f"\n📸 Publishing to Instagram Reels: {video_path.name}")
        queue_mgr = InstagramQueueManager()
        # Copy to inbox and process
        inbox_dir = PROJECT_ROOT / "reels_inbox"
        inbox_dir.mkdir(exist_ok=True)
        target = inbox_dir / video_path.name
        import shutil
        shutil.copy(str(video_path), str(target))
        res = queue_mgr.process_video_file(target, dry_run=args.dry_run)
        print(f"Result: {res}")
    elif platform in ["youtube", "yt"]:
        print(f"\n▶️ Publishing to YouTube Shorts: {video_path.name}")
        if not YouTubeAuthenticator.is_authenticated():
            print("⚠️ YouTube channel not authorized. Run 'python3 autoreel.py auth-youtube' first.")
            return
        pub = YouTubePublisher()
        title = args.title or video_path.stem.replace("_", " ")
        res = pub.upload_short(video_path, title=title, privacy_status="public" if not args.dry_run else "private")
        print(f"Result: {res}")

def cmd_auto(args):
    """
    1-Click Autonomous Multi-Platform Pipeline:
    Idea Queue -> Daily Quota Check -> Video Generation -> CDN Prep -> Instagram & YouTube Publishing.
    """
    allowed, remaining, msg = QuotaGovernor.can_generate()
    if not allowed:
        print(f"\n{msg}")
        return

    print("🚀 [AutoReelStudio] Starting Full Autonomous Production & Distribution Run...")
    if args.prompt:
        idea = IdeaResearchEngine._synthesize_from_custom_prompt(args.prompt, duration=args.duration)
    else:
        idea = IdeaQueueManager.pop_next_idea(auto_replenish=True)
        if not idea:
            IdeaQueueManager.replenish_if_needed()
            idea = IdeaQueueManager.pop_next_idea(auto_replenish=True)

    video_path, telemetry = asyncio.run(VideoGenerator.generate_reel(idea=idea))

    # CDN Optimization
    print("\n⚙️ [AutoReelStudio] Optimizing for CDN Streaming...")
    cdn_video = CDNOptimizer.optimize_for_cdn(video_path)

    # Packaging Metadata
    ig_meta = MetadataPackager.package_for_instagram(
        title=idea.get("title", ""),
        genre=idea.get("genre", "science"),
        hook=idea.get("hook", ""),
        facts=idea.get("facts", ""),
        payoff=idea.get("payoff", "")
    )
    yt_meta = MetadataPackager.package_for_youtube(
        title=idea.get("title", ""),
        genre=idea.get("genre", "science"),
        hook=idea.get("hook", ""),
        facts=idea.get("facts", ""),
        payoff=idea.get("payoff", "")
    )

    dest = args.target.lower()

    # Publish to Instagram
    if dest in ["instagram", "both", "all"]:
        print("\n📸 [AutoReelStudio] Dispatching to Instagram Reels...")
        inbox_dir = PROJECT_ROOT / "reels_inbox"
        inbox_dir.mkdir(exist_ok=True)
        target = inbox_dir / cdn_video.name
        import shutil
        shutil.copy(str(cdn_video), str(target))
        # Write companion caption
        with open(target.with_suffix(".txt"), "w", encoding="utf-8") as f:
            f.write(ig_meta["caption"])
        queue_mgr = InstagramQueueManager()
        res_ig = queue_mgr.process_video_file(target, dry_run=args.dry_run)
        print(f"Instagram Result: {res_ig}")

    # Publish to YouTube Shorts
    if dest in ["youtube", "both", "all"]:
        print("\n▶️ [AutoReelStudio] Dispatching to YouTube Shorts...")
        if not YouTubeAuthenticator.is_authenticated():
            print("⚠️ YouTube not authenticated. Run 'python3 autoreel.py auth-youtube' to connect.")
        else:
            pub = YouTubePublisher()
            res_yt = pub.upload_short(
                video_path=cdn_video,
                title=yt_meta["title"],
                description=yt_meta["description"],
                tags=yt_meta["tags"],
                privacy_status="public" if not args.dry_run else "private"
            )
            print(f"YouTube Result: {res_yt}")

def cmd_auth_youtube(args):
    """Starts local server to complete OAuth 2.0 authorization for YouTube."""
    YouTubeAuthenticator.run_local_auth_server(timeout_secs=args.timeout)

def cmd_studio(args):
    """Starts the AutoReelStudio Web Interface."""
    from server import start_server
    port = args.port or int(os.environ.get("PORT", 8080))
    start_server(port=port)

# ==============================================================================
# MAIN CLI DISPATCHER
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="autoreel",
        description="AutoReelStudio: Autonomous 4-Stage Multi-Platform Video Production & Social Publisher",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="AutoReelStudio Commands")

    # Command: queue
    p_queue = subparsers.add_parser("queue", aliases=["ideas"], help="Inspect and manage the 10-15 idea buffer queue")
    p_queue.add_argument("action", nargs="?", default="list", choices=["list", "replenish", "pop"], help="Queue action")

    # Command: quota
    subparsers.add_parser("quota", help="Check today's 50-reels generation quota telemetry")

    # Command: make
    p_make = subparsers.add_parser("make", aliases=["generate"], help="Synthesize video from idea queue or custom prompt with AI visuals")
    p_make.add_argument("-p", "--prompt", default=None, help="Custom prompt (or leave empty to pop from idea queue)")
    p_make.add_argument("-d", "--duration", type=int, choices=[10, 15, 30, 60], default=15, help="Video duration in seconds")
    p_make.add_argument("-v", "--voice", default=None, help="Voice actor override")
    p_make.add_argument("-m", "--music", default=None, help="Music style override")
    p_make.add_argument("-c", "--caption-style", default=None, choices=["karaoke", "high_impact", "clean_minimal", "cinematic"], help="Subtitle style")
    p_make.add_argument("--skip-cdn", action="store_true", help="Skip CDN faststart optimization")

    # Command: process
    p_proc = subparsers.add_parser("process", help="CDN video optimization and metadata packaging")
    p_proc.add_argument("video", help="Path to input MP4 video file")

    # Command: publish
    p_pub = subparsers.add_parser("publish", help="Publish video to Instagram Reels or YouTube Shorts")
    p_pub.add_argument("platform", choices=["instagram", "ig", "youtube", "yt"], help="Target platform")
    p_pub.add_argument("video", help="Path to video file")
    p_pub.add_argument("--title", default=None, help="Optional title")
    p_pub.add_argument("--dry-run", action="store_true", help="Simulate API upload in dry-run mode")

    # Command: auto
    p_auto = subparsers.add_parser("auto", help="1-Click end-to-end: Idea -> Quota Check -> Video -> CDN -> Multi-Platform Publish")
    p_auto.add_argument("-p", "--prompt", default=None, help="Custom prompt or leave empty to consume from 10-15 buffer queue")
    p_auto.add_argument("-d", "--duration", type=int, default=15, choices=[10, 15, 30, 60], help="Duration")
    p_auto.add_argument("--target", default="both", choices=["both", "instagram", "youtube", "all"], help="Publish destination")
    p_auto.add_argument("--dry-run", action="store_true", help="Simulate publishing APIs")

    # Command: auth-youtube
    p_auth = subparsers.add_parser("auth-youtube", help="Authorize YouTube channel via Google OAuth 2.0 (port 8000)")
    p_auth.add_argument("--timeout", type=int, default=180, help="Timeout in seconds")

    # Command: studio
    p_studio = subparsers.add_parser("studio", aliases=["web", "ui"], help="Start AutoReelStudio Web Dashboard")
    p_studio.add_argument("--port", type=int, default=8080, help="Web server port (default: 8080)")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command in ["queue", "ideas"]:
        cmd_queue(args)
    elif args.command == "quota":
        cmd_quota(args)
    elif args.command in ["make", "generate"]:
        cmd_make(args)
    elif args.command == "process":
        cmd_process(args)
    elif args.command == "publish":
        cmd_publish(args)
    elif args.command == "auto":
        cmd_auto(args)
    elif args.command == "auth-youtube":
        cmd_auth_youtube(args)
    elif args.command in ["studio", "web", "ui"]:
        cmd_studio(args)

if __name__ == "__main__":
    main()
