#!/usr/bin/env python3
"""
AutoReelStudio — Unified Autonomous AI Video Generation & Social Publishing Platform
Modular Architecture:
  1. idea_generation/  -> Research, Ideation, 10-15 Buffer Queue, Feedback Learner
  2. video_generation/ -> AI Visuals, Natural Voice, Ducked Audio, 10/day Quota Gate, Composer
  3. video_processing/ -> CDN Video Optimization (faststart), Metadata Packager (IG + YT)
  4. publishers/       -> Dedicated Platform Publishers (Instagram Meta Graph API + YouTube Data API v3)
"""

import sys
import os
from pathlib import Path

# Auto-switch into project virtual environment if executed with system python
PROJECT_ROOT = Path(__file__).resolve().parent
_venv_dir = PROJECT_ROOT / "venv"
_venv_python = _venv_dir / "bin" / "python3"
if _venv_python.exists() and sys.prefix != str(_venv_dir):
    if os.environ.get("_AUTOREEL_VENV_ACTIVE") != "1":
        os.environ["_AUTOREEL_VENV_ACTIVE"] = "1"
        try:
            os.execv(str(_venv_python), [str(_venv_python)] + sys.argv)
        except Exception:
            pass

import argparse
import asyncio

# Add project root to sys.path
sys.path.insert(0, str(PROJECT_ROOT))

from idea_generation import IdeaQueueManager, IdeaResearchEngine, FeedbackLearner
from video_generation import VideoGenerator, QuotaGovernor, DAILY_MAX_REELS
from video_processing import CDNOptimizer, MetadataPackager
from publishers import (
    InstagramPublisher,
    InstagramQueueManager,
    YouTubePublisher,
    YouTubeAuthenticator,
    PublishingQueueManager
)

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
    """Displays today's 10-reels generation quota telemetry."""
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
        if res.get("success"):
            from publishers.recent_manager import RecentlyPublishedManager
            import uuid
            from datetime import datetime, timezone
            RecentlyPublishedManager.record_published({
                "id": f"pub_{uuid.uuid4().hex[:10]}",
                "title": args.title or video_path.stem.replace("_", " "),
                "filename": video_path.name,
                "video_path": str(video_path),
                "platforms": ["instagram"],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "receipts": {"instagram": res.get("receipt", {})}
            })
    elif platform in ["youtube", "yt"]:
        print(f"\n▶️ Publishing to YouTube Shorts: {video_path.name}")
        if not YouTubeAuthenticator.is_authenticated():
            print("⚠️ YouTube channel not authorized. Run 'python3 autoreel.py auth-youtube' first.")
            return
        pub = YouTubePublisher()
        title = args.title or video_path.stem.replace("_", " ")
        privacy = args.privacy if not args.dry_run else "private"
        res = pub.upload_short(video_path, title=title, privacy_status=privacy)
        print(f"Result: {res}")
        if res.get("success"):
            from publishers.recent_manager import RecentlyPublishedManager
            import uuid
            from datetime import datetime, timezone
            RecentlyPublishedManager.record_published({
                "id": f"pub_{uuid.uuid4().hex[:10]}",
                "title": title,
                "filename": video_path.name,
                "video_path": str(video_path),
                "platforms": ["youtube"],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "receipts": {"youtube": res}
            })

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

    # Check if user requested immediate upload or scheduled queue pacing
    if not getattr(args, "now", False):
        print("\n📥 [AutoReelStudio] Enqueueing to Ready Videos Publishing Queue (Paced Distribution)...")
        platforms = ["instagram", "youtube"] if dest in ["both", "all"] else [dest]
        entry = PublishingQueueManager.enqueue(
            video_path=cdn_video,
            title=idea.get("title", cdn_video.stem),
            platforms=platforms,
            instagram_meta=ig_meta,
            youtube_meta=yt_meta
        )
        print("=" * 65)
        print(f"✅ VIDEO READY & ENQUEUED: {entry['title']}")
        print(f"🔑 Queue ID:        {entry['id']}")
        print(f"⏰ Scheduled Time:  {entry['scheduled_time']} (Paced 10 reels/day)")
        print(f"🎯 Targets:         {', '.join(platforms).upper()}")
        print(f"⚡ To upload right now: python3 autoreel.py upload-now {entry['id']}")
        print("=" * 65)
        return

    # Instant live upload (when --now flag is passed)
    print("\n⚡ [AutoReelStudio] Immediate Upload (--now requested)...")

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

    # Record to recently published if successful
    receipts = {}
    if 'res_ig' in locals() and res_ig and res_ig.get("success"):
        receipts["instagram"] = res_ig.get("receipt", {})
    if 'res_yt' in locals() and res_yt and res_yt.get("success"):
        receipts["youtube"] = res_yt
    if receipts:
        from publishers.recent_manager import RecentlyPublishedManager
        import uuid
        from datetime import datetime, timezone
        RecentlyPublishedManager.record_published({
            "id": f"pub_{uuid.uuid4().hex[:10]}",
            "title": idea.get("title", cdn_video.stem),
            "filename": cdn_video.name,
            "video_path": str(cdn_video),
            "platforms": [dest] if dest not in ["both", "all"] else ["instagram", "youtube"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "receipts": receipts
        })

def cmd_pub_queue(args):
    """Inspects the scheduled ready video publishing queue."""
    if getattr(args, "action", None) == "due":
        print("⏰ Checking and releasing any due scheduled videos...")
        res = PublishingQueueManager.process_due_items(dry_run=args.dry_run)
        print(f"Released {len(res)} due items.")
        return
    if getattr(args, "action", None) == "clear":
        removed = PublishingQueueManager.clear_completed()
        print(f"🧹 Purged {removed} completed/cancelled entries from queue.")
        return

    items = PublishingQueueManager.get_queue()
    print("\n" + "=" * 65)
    print(f"🚀 READY VIDEOS PUBLISHING QUEUE ({len(items)} items)")
    print("   Pacing: 10 reels/day distribution (~2.4 hr intervals)")
    print("=" * 65)
    if not items:
        print("  (Publishing queue is empty. Generated videos queue here for scheduled pacing)")
    for idx, item in enumerate(items, 1):
        status = item.get("status", "unknown").upper()
        platforms = "/".join(item.get("platforms", []))
        sched = item.get("scheduled_time", "N/A")
        print(f"  {idx:02d}. [{status:10s}] {item.get('title')}")
        print(f"      ID: {item.get('id')} | Targets: {platforms} | Scheduled: {sched}")
    print("=" * 65)

def cmd_upload_now(args):
    """1-Click Upload Now: Bypasses the schedule timer to publish immediately."""
    item_id = args.id
    dry_run = args.dry_run
    if item_id and item_id != "next":
        res = PublishingQueueManager.publish_now(item_id, dry_run=dry_run, is_manual=True)
    else:
        res = PublishingQueueManager.publish_next(dry_run=dry_run, is_manual=True)

    if res:
        print("\n" + "=" * 65)
        print(f"⚡ 1-Click Upload Result: {res.get('status', '').upper()}")
        print(f"🔑 ID:        {res.get('id')}")
        print(f"🧾 Receipts:  {res.get('receipts')}")
        if res.get("errors"):
            print(f"⚠️ Errors:    {res.get('errors')}")
        print("=" * 65)
    else:
        print("\n⚠️ No pending videos waiting in the publishing queue.")

def cmd_published(args):
    """Lists the last 10 published reels and their live URLs (rolling window)."""
    from publishers.recent_manager import RecentlyPublishedManager
    items = RecentlyPublishedManager.get_recent(limit=10)
    print("\n" + "=" * 65)
    print(f"🎬 RECENTLY PUBLISHED REELS (Last 10 Rolling Buffer)")
    print("   Rule: Only the last 10 published reels are kept. Older reels are deleted forever.")
    print("=" * 65)
    if not items:
        print("  (No published reels in archive yet)")
    for idx, item in enumerate(items, 1):
        print(f"  {idx:02d}. {item.get('title')}")
        print(f"      Published At: {item.get('published_at')}")
        if item.get("instagram_permalink"):
            print(f"      📸 Instagram:  {item['instagram_permalink']}")
        if item.get("youtube_shorts_url"):
            print(f"      ▶️ YouTube:    {item['youtube_shorts_url']}")
    print("=" * 65)

def cmd_scheduler(args):
    """Runs continuous background scheduler loop checking every interval."""
    print("⏰ [AutoReelStudio Scheduler Daemon] Starting paced release loop (checking every 30s)...")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            PublishingQueueManager.process_due_items(dry_run=args.dry_run)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nScheduler daemon stopped.")

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

def cmd_check_meta(args):
    """Diagnoses Instagram Meta Graph API connectivity and permissions."""
    from publishers.instagram.publisher import MetaGraphPublisher
    from publishers.instagram.config import META_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
    print("\n" + "=" * 65)
    print("🔍 META GRAPH API (INSTAGRAM REELS) DIAGNOSTIC")
    print("=" * 65)
    print(f"📌 Account ID:  {INSTAGRAM_ACCOUNT_ID}")
    print(f"🔑 Token:       {META_ACCESS_TOKEN[:15]}..." if META_ACCESS_TOKEN else "❌ No token in .env")
    pub = MetaGraphPublisher()
    acc = pub.get_account_info()
    if acc.get("authenticated"):
        print("✅ Meta Graph API: CONNECTED & VALID")
        print(f"👤 Username:      @{acc.get('username')}")
        limit = pub.get_publishing_limit()
        print(f"📊 24h Quota:     {limit.get('quota_usage', 0)}/{limit.get('quota_total', 100)} used")
    else:
        print("❌ Meta Graph API: ACCESS BLOCKED / INVALID")
        print(f"⚠️ Error:         {acc.get('error')}")
        print("\n💡 Resolution Steps:")
        print("  1. Visit Meta Graph API Explorer: https://developers.facebook.com/tools/explorer/")
        print("  2. Select your App & Page, add scopes: instagram_basic, instagram_content_publish, pages_show_list")
        print("  3. Generate token & run: python3 autoreel.py set-meta-token <your_token>")
    print("=" * 65 + "\n")

def cmd_set_meta_token(args):
    """Updates META_ACCESS_TOKEN in .env and tests it immediately."""
    new_token = args.token.strip()
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        lines = []
        replaced = False
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("META_ACCESS_TOKEN="):
                    lines.append(f'META_ACCESS_TOKEN="{new_token}"\n')
                    replaced = True
                else:
                    lines.append(line)
        if not replaced:
            lines.append(f'META_ACCESS_TOKEN="{new_token}"\n')
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    os.environ["META_ACCESS_TOKEN"] = new_token
    print(f"✅ Updated META_ACCESS_TOKEN in {env_path}")
    from publishers.instagram.publisher import MetaGraphPublisher
    pub = MetaGraphPublisher(access_token=new_token)
    acc = pub.get_account_info()
    if acc.get("authenticated"):
        print(f"🎉 Verified! Connected to @{acc.get('username')} (ID: {acc.get('id')})")
    else:
        print(f"⚠️ Token saved, but Meta returned: {acc.get('error')}")

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
    subparsers.add_parser("quota", help="Check today's 10-reels generation quota telemetry")

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
    p_pub.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="YouTube privacy status (default: public)")
    p_pub.add_argument("--dry-run", action="store_true", help="Simulate API upload in dry-run mode")

    # Command: auto
    p_auto = subparsers.add_parser("auto", help="1-Click end-to-end: Idea -> Quota Check -> Video -> CDN -> Multi-Platform Publish")
    p_auto.add_argument("-p", "--prompt", default=None, help="Custom prompt or leave empty to consume from 10-15 buffer queue")
    p_auto.add_argument("-d", "--duration", type=int, default=15, choices=[10, 15, 30, 60], help="Duration")
    p_auto.add_argument("--target", default="both", choices=["both", "instagram", "youtube", "all"], help="Publish destination")
    p_auto.add_argument("--now", action="store_true", help="Immediately publish now instead of enqueueing for paced scheduling")
    p_auto.add_argument("--dry-run", action="store_true", help="Simulate publishing APIs")

    # Command: pub-queue (Ready videos publishing queue)
    p_pq = subparsers.add_parser("pub-queue", aliases=["ready-queue", "scheduled"], help="Inspect ready videos scheduled publishing queue")
    p_pq.add_argument("action", nargs="?", default="list", choices=["list", "due", "clear"], help="Action to perform")
    p_pq.add_argument("--dry-run", action="store_true", help="Simulate releases in dry-run mode")

    # Command: upload-now (1-Click instant upload bypass)
    p_un = subparsers.add_parser("upload-now", aliases=["publish-now"], help="1-Click Upload Now: Bypasses schedule timer to publish immediately")
    p_un.add_argument("id", nargs="?", default="next", help="Queue item ID or 'next' for earliest")
    p_un.add_argument("--dry-run", action="store_true", help="Simulate upload in dry-run mode")

    # Command: published (Recently published reels rolling buffer)
    subparsers.add_parser("published", aliases=["recent"], help="List the last 10 published reels (rolling buffer)")

    # Command: daemon / scheduler
    p_sched = subparsers.add_parser("daemon", aliases=["scheduler"], help="Start background scheduler daemon for paced releases")
    p_sched.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    p_sched.add_argument("--dry-run", action="store_true", help="Simulate releases in dry-run mode")

    # Command: auth-youtube
    p_auth = subparsers.add_parser("auth-youtube", help="Authorize YouTube channel via Google OAuth 2.0 (port 8000)")
    p_auth.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")

    # Command: check-meta
    p_meta = subparsers.add_parser("check-meta", aliases=["test-meta", "meta"], help="Test Meta Instagram Graph API status and permissions")

    # Command: set-meta-token
    p_set_token = subparsers.add_parser("set-meta-token", help="Update META_ACCESS_TOKEN in .env and test it")
    p_set_token.add_argument("token", type=str, help="Fresh Meta Long-Lived User or Page Access Token")

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
    elif args.command in ["pub-queue", "ready-queue", "scheduled"]:
        cmd_pub_queue(args)
    elif args.command in ["upload-now", "publish-now"]:
        cmd_upload_now(args)
    elif args.command in ["published", "recent"]:
        cmd_published(args)
    elif args.command in ["daemon", "scheduler"]:
        cmd_scheduler(args)
    elif args.command == "auth-youtube":
        cmd_auth_youtube(args)
    elif args.command in ["check-meta", "test-meta", "meta"]:
        cmd_check_meta(args)
    elif args.command == "set-meta-token":
        cmd_set_meta_token(args)
    elif args.command in ["studio", "web", "ui"]:
        cmd_studio(args)

if __name__ == "__main__":
    main()
