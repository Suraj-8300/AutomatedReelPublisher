#!/usr/bin/env python3
import sys
import argparse
import asyncio
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import VOICES, DEFAULT_VOICE, DURATION_TARGETS, OUTPUT_DIR
from core.idea_generator import list_all_topics
from core.prompt_enhancer import PromptEnhancer
from core.tts_engine import TTSEngine
from core.music_engine import MusicEngine
from core.subtitle_engine import SubtitleEngine
from core.video_composer import VideoComposer

async def run_pipeline(
    prompt: str = None,
    duration: int = 15,
    voice: str = DEFAULT_VOICE,
    music_style: str = "cyber_pulse",
    theme: str = None
) -> str:
    start_time = time.time()
    print("=" * 60)
    print("🎬  VIRAL REEL AI - MULTI-TOPIC VIDEO GENERATION PIPELINE")
    print("=" * 60)

    # 1. Prompt Enhancement & Storyboarding
    print(f"\n[1/5] 💡 Enhancing Prompt & Storyboard (Target: {duration}s)...")
    storyboard = PromptEnhancer.enhance(user_prompt=prompt, duration=duration, theme=theme)
    print(f"      📌 Topic:    {storyboard['title']}")
    print(f"      🏷️ Category: {storyboard['category']}")
    print(f"      🎨 Theme:    {storyboard['theme']}")
    print(f"      📝 Script:   \"{storyboard['script'][:90]}...\"")

    # 2. Neural Voiceover Synthesis
    speech_rate = "+12%" if duration == 10 else ("+6%" if duration == 15 else "+0%")
    print(f"\n[2/5] 🎙️ Synthesizing Voiceover & Captions ({voice}, rate={speech_rate})...")
    voice_info = await TTSEngine.synthesize(
        text=storyboard["script"],
        voice=voice,
        rate=speech_rate
    )
    print(f"      🔊 Audio Duration: {voice_info['duration']:.2f}s")
    print(f"      ⏱️ Word Timings:   {len(voice_info['words'])} words mapped")

    # 3. Royalty-Free Music Generation
    total_reel_duration = max(voice_info["duration"] + 0.5, float(duration))
    print(f"\n[3/5] 🎵 Generating Procedural Soundtrack ({music_style}, {total_reel_duration:.1f}s)...")
    music_file = MusicEngine.generate_soundtrack(
        duration=total_reel_duration,
        style=music_style
    )
    print(f"      🎶 Music Track: {Path(music_file).name}")

    # 4. Animated Reel Captions (ASS)
    print(f"\n[4/5] ✍️ Building Word-by-Word Highlighted Subtitles...")
    highlight_color = "#FFE600" if storyboard["theme"] != "cosmic_purple" else "#00FFA3"
    ass_file = SubtitleEngine.generate_ass(
        words=voice_info["words"],
        highlight_color=highlight_color,
        words_per_chunk=3
    )
    print(f"      📜 Subtitles: {Path(ass_file).name}")

    # 5. Visual Rendering & Master Assembly
    print(f"\n[5/5] 🎥 Assembling 9:16 Vertical Video (1080x1920 @ 30fps)...")
    output_mp4 = VideoComposer.compose_reel(
        storyboard=storyboard,
        voice_info=voice_info,
        music_file=music_file,
        ass_subtitle_file=ass_file
    )

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 VIDEO READY FOR UPLOAD!")
    print(f"📁 Output Path: {output_mp4}")
    print(f"⚡ Total Processing Time: {elapsed:.2f}s")
    print(f"📐 Specs: 1080x1920 (9:16 Vertical), H.264 + AAC Stereo")
    print("=" * 60)

    return output_mp4

def send_to_instagram_inbox(output_mp4: str, storyboard: dict, auto_publish: bool = False, dry_run: bool = False):
    import shutil
    from instagram_pipeline.config import INBOX_DIR
    from instagram_pipeline.metadata_linker import MetadataLinker
    from instagram_pipeline.queue_manager import ReelQueueManager

    video_path = Path(output_mp4)
    target_video = INBOX_DIR / video_path.name
    shutil.copy(str(video_path), str(target_video))

    # Generate companion metadata
    caption = MetadataLinker.generate_caption_from_title(storyboard.get("title", video_path.stem))
    target_caption = INBOX_DIR / f"{video_path.stem}.txt"
    with open(target_caption, "w", encoding="utf-8") as f:
        f.write(caption)

    print(f"\n📥 Queued to Instagram Inbox: {target_video.name}")
    print(f"📝 Linked Caption File:      {target_caption.name}")

    if auto_publish:
        print("\n🚀 Auto-Publishing to Instagram Reels...")
        manager = ReelQueueManager()
        manager.process_video_file(target_video, dry_run=dry_run)

def main():
    parser = argparse.ArgumentParser(description="Is It Plausible - Automated 10s/15s/30s/60s Social Video Generator")
    parser.add_argument("-p", "--prompt", type=str, default=None, help="Custom prompt or myth to investigate (or leave empty for 1-click auto idea)")
    parser.add_argument("-d", "--duration", type=int, choices=[10, 15, 30, 60], default=15, help="Video duration in seconds (10, 15, 30, or 60)")
    parser.add_argument("-v", "--voice", type=str, default=DEFAULT_VOICE, help=f"Voice model (default: {DEFAULT_VOICE})")
    parser.add_argument("-m", "--music", type=str, default="cyber_pulse", choices=["cyber_pulse", "deep_mystery", "curiosity_lofi", "cinematic_drive"], help="Soundtrack style")
    parser.add_argument("-t", "--theme", type=str, default=None, choices=["cyber_blue", "cosmic_purple", "deep_emerald", "crimson_flame"], help="Color theme")
    parser.add_argument("--to-inbox", action="store_true", help="Automatically queue generated video into Instagram Reels inbox")
    parser.add_argument("--publish", action="store_true", help="Automatically publish to Instagram Reels immediately upon generation")
    parser.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing in dry-run mode")
    parser.add_argument("--list-topics", action="store_true", help="List pre-built viral topics and exit")

    args = parser.parse_args()

    if args.list_topics:
        print("\nAvailable Viral Pre-built Topics:")
        for t in list_all_topics():
            print(f"  • {t}")
        return

    output_video = asyncio.run(run_pipeline(
        prompt=args.prompt,
        duration=args.duration,
        voice=args.voice,
        music_style=args.music,
        theme=args.theme
    ))

    if args.to_inbox or args.publish:
        from core.prompt_enhancer import PromptEnhancer
        storyboard = PromptEnhancer.enhance(user_prompt=args.prompt, duration=args.duration, theme=args.theme)
        send_to_instagram_inbox(
            output_mp4=output_video,
            storyboard=storyboard,
            auto_publish=args.publish,
            dry_run=args.dry_run
        )

if __name__ == "__main__":
    main()
