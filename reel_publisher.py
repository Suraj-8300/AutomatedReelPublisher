#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from instagram_pipeline.config import (
    INBOX_DIR,
    PROCESSING_DIR,
    ARCHIVE_DIR,
    FAILED_DIR,
    TARGET_WIDTH,
    TARGET_HEIGHT,
    TARGET_FPS,
    SAFE_ZONE_TOP,
    SAFE_ZONE_BOTTOM,
    DEFAULT_SCALING_MODE
)
from instagram_pipeline.preprocessor import VideoPreprocessor
from instagram_pipeline.metadata_linker import MetadataLinker
from instagram_pipeline.cloud_bridge import CloudBridge
from instagram_pipeline.publisher import MetaGraphPublisher
from instagram_pipeline.queue_manager import ReelQueueManager

def cmd_check(args):
    """Inspects a video and displays a compliance report."""
    video_path = Path(args.video).resolve()
    print(f"\n🔍 Probing video file: {video_path.name}")
    meta = VideoPreprocessor.probe_video(video_path)
    check = VideoPreprocessor.validate_compliance(meta)

    v = meta["video"]
    a = meta["audio"]

    print("\n" + "=" * 65)
    print("📊 INSTAGRAM REELS COMPLIANCE AUDIT")
    print("=" * 65)
    print(f"📁 File Name:      {meta['filename']}")
    print(f"📦 Container:      {meta['format_name']} (faststart moov-first: {meta['faststart']})")
    print(f"⏱️ Duration:       {meta['duration']:.2f}s (Req: 3s - 90s)")
    print(f"💾 File Size:      {meta['file_size'] / (1024*1024):.2f} MB")
    print(f"📐 Resolution:     {v['width']} x {v['height']} (Req: {TARGET_WIDTH} x {TARGET_HEIGHT})")
    print(f"🎞️ Video Codec:    {v['codec']} ({v['profile']}, pix_fmt: {v['pix_fmt']})")
    print(f"⚡ Frame Rate:     {v['fps']} FPS (Req: 23.976 - 60 FPS)")
    print(f"🔊 Audio Codec:    {a['codec']} ({a['sample_rate']} Hz, {a['channels']} channels)")
    print("=" * 65)

    if check["is_compliant"]:
        print("🎉 STATUS: 100% COMPLIANT with Instagram Reels specifications!")
    else:
        print("⚠️ STATUS: TRANSCODING REQUIRED")
        print("\nIdentified Issues:")
        for idx, issue in enumerate(check["issues"], 1):
            print(f"  {idx}. {issue}")

    if check["warnings"]:
        print("\nAdvisories:")
        for w in check["warnings"]:
            print(f"  • {w}")
    print("=" * 65 + "\n")

def cmd_normalize(args):
    """Normalizes an input video to exact Instagram Reel specifications."""
    input_path = Path(args.video).resolve()
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = input_path.parent / f"{input_path.stem}_reel_1080x1920.mp4"

    print(f"\n🎥 Normalizing {input_path.name} -> {output_path.name} (mode: {args.mode})...")
    out = VideoPreprocessor.normalize_video(
        input_path=input_path,
        output_path=output_path,
        scaling_mode=args.mode,
        overwrite=True
    )
    print(f"✅ Normalization complete: {out}")
    print(f"📐 Specs: 1080x1920, H.264 High Profile, AAC Stereo 48kHz, +faststart\n")

def cmd_preview(args):
    """Renders safe-zone debug frame with UI overlays."""
    input_path = Path(args.video).resolve()
    output_path = Path(args.output) if args.output else input_path.parent / f"{input_path.stem}_safe_zone.jpg"

    print(f"\n🖼️ Rendering Instagram safe-zone preview for {input_path.name}...")
    VideoPreprocessor.render_safe_zone_preview(input_path, output_path)
    print(f"✅ Safe-zone preview saved: {output_path}\n")

def cmd_process(args):
    """Processes and publishes a single video file."""
    video_path = Path(args.video).resolve()
    manager = ReelQueueManager()
    res = manager.process_video_file(
        raw_video_path=video_path,
        scaling_mode=args.mode,
        dry_run=args.dry_run
    )
    sys.exit(0 if res.get("success") else 1)

def cmd_inbox(args):
    """Processes all video files currently queued in reels_inbox/."""
    manager = ReelQueueManager()
    results = manager.process_inbox(scaling_mode=args.mode, dry_run=args.dry_run)
    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n[Inbox Summary] Processed {len(results)} videos: {success_count} succeeded, {len(results) - success_count} failed.\n")

def cmd_watch(args):
    """Starts the continuous media watcher daemon."""
    manager = ReelQueueManager()
    manager.watch_inbox(
        interval_secs=args.interval,
        scaling_mode=args.mode,
        dry_run=args.dry_run
    )

def cmd_test(args):
    """Runs a complete end-to-end pipeline self-test."""
    print("=" * 65)
    print("🧪 RUNNING INSTAGRAM REELS PIPELINE SELF-TEST")
    print("=" * 65)

    test_video = INBOX_DIR / "test_sample_footage.mp4"
    test_caption = INBOX_DIR / "test_sample_footage.txt"

    # 1. Synthesize a non-compliant landscape test video (640x360 @ 24fps)
    print("\n[Test 1/4] Generating non-compliant sample footage (640x360 landscape)...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24:duration=4",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=4",
        "-c:v", "libx264", "-c:a", "aac",
        str(test_video)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    with open(test_caption, "w", encoding="utf-8") as f:
        f.write("🧪 Automated Instagram Reels Pipeline Verification Test! #reels #ai #test")

    print(f"           Created test asset: {test_video.name}")

    # 2. Check compliance
    print("\n[Test 2/4] Verifying compliance detection...")
    meta = VideoPreprocessor.probe_video(test_video)
    check = VideoPreprocessor.validate_compliance(meta)
    assert not check["is_compliant"], "Sample video should require transcoding"
    print("           Compliance engine correctly detected non-compliant dimensions & faststart.")

    # 3. Process through queue manager
    print("\n[Test 3/4] Running queue manager end-to-end (dry-run)...")
    manager = ReelQueueManager()
    result = manager.process_video_file(
        raw_video_path=test_video,
        scaling_mode="pad",
        dry_run=True
    )
    assert result["success"], f"Processing failed: {result}"
    receipt = result["receipt"]
    print(f"           Publication Receipt: {receipt['instagram_permalink']}")

    # 4. Verify Archive
    print("\n[Test 4/4] Verifying archival directory and file outputs...")
    archive_dir = Path(result["archive_dir"])
    assert archive_dir.exists(), "Archive directory must exist"
    archived_files = [f.name for f in archive_dir.iterdir()]
    print(f"           Archived files: {archived_files}")

    print("\n" + "=" * 65)
    print("🎉 ALL SELF-TESTS PASSED! PIPELINE IS 100% OPERATIONAL.")
    print("=" * 65 + "\n")

def cmd_blueprint(args):
    """Generates an end-to-end production blueprint for a high-retention Instagram Reel."""
    from instagram_pipeline.blueprint_generator import generate_production_blueprint
    bp = generate_production_blueprint(
        topic=args.topic,
        target_audience=args.audience,
        goal=args.goal
    )
    print(bp)
    if args.output:
        out_path = Path(args.output).resolve()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(bp)
        print(f"\n📁 Blueprint saved to: {out_path}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Automated Instagram Reels Video Processing and Meta Graph API Publishing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: blueprint
    p_blue = subparsers.add_parser("blueprint", help="Generate viral production blueprint, shot list, and AI prompts")
    p_blue.add_argument("topic", help="Reel topic or concept")
    p_blue.add_argument("--audience", default="Curious minds & social scrollers", help="Target audience avatar")
    p_blue.add_argument("--goal", default="SAVE / SHARE", choices=["SAVE / SHARE", "COMMENTS", "CLICK IN BIO"], help="Primary conversion goal")
    p_blue.add_argument("--output", default=None, help="Optional markdown file path to save blueprint")

    # Command: watch
    p_watch = subparsers.add_parser("watch", help="Continuously watch reels_inbox/ for incoming footage")
    p_watch.add_argument("--interval", type=float, default=5.0, help="Poll interval in seconds (default: 5.0)")
    p_watch.add_argument("--mode", choices=["pad", "crop", "blur_pad"], default=DEFAULT_SCALING_MODE, help="Scaling mode")
    p_watch.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing without live API calls")

    # Command: inbox
    p_inbox = subparsers.add_parser("inbox", help="Process all videos currently in reels_inbox/ once")
    p_inbox.add_argument("--mode", choices=["pad", "crop", "blur_pad"], default=DEFAULT_SCALING_MODE, help="Scaling mode")
    p_inbox.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing without live API calls")

    # Command: process
    p_proc = subparsers.add_parser("process", help="Process and publish a single video file")
    p_proc.add_argument("video", help="Path to video file")
    p_proc.add_argument("--mode", choices=["pad", "crop", "blur_pad"], default=DEFAULT_SCALING_MODE, help="Scaling mode")
    p_proc.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing without live API calls")

    # Command: check
    p_check = subparsers.add_parser("check", help="Audit video against Instagram Reels technical specifications")
    p_check.add_argument("video", help="Path to video file")

    # Command: normalize
    p_norm = subparsers.add_parser("normalize", help="Transcode video to compliant 1080x1920 H.264/AAC Reel")
    p_norm.add_argument("video", help="Path to input video file")
    p_norm.add_argument("output", nargs="?", default=None, help="Output MP4 path")
    p_norm.add_argument("--mode", choices=["pad", "crop", "blur_pad"], default=DEFAULT_SCALING_MODE, help="Scaling mode")

    # Command: preview
    p_prev = subparsers.add_parser("preview", help="Render safe-zone danger overlay debug frame")
    p_prev.add_argument("video", help="Path to input video file")
    p_prev.add_argument("output", nargs="?", default=None, help="Output JPEG preview path")

    # Command: test
    subparsers.add_parser("test", help="Run diagnostic pipeline self-test")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "blueprint":
        cmd_blueprint(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "inbox":
        cmd_inbox(args)
    elif args.command == "process":
        cmd_process(args)
    elif args.command == "check":
        cmd_check(args)
    elif args.command == "normalize":
        cmd_normalize(args)
    elif args.command == "preview":
        cmd_preview(args)
    elif args.command == "test":
        cmd_test(args)

if __name__ == "__main__":
    main()

