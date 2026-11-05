#!/usr/bin/env python3
import sys
import argparse
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config import VOICES, DEFAULT_VOICE, OUTPUT_DIR
from core.creative_randomizer import GENRE_TAXONOMY, GENERATION_MODES
from core.genre_catalog import get_catalog_topics
from core.prompt_enhancer import PromptEnhancer
from core.tts_engine import TTSEngine
from core.music_engine import MusicEngine
from core.subtitle_engine import SubtitleEngine
from core.video_composer import VideoComposer
from core.content_history import ContentHistory
from core.quality_control import QualityControlEngine

async def run_pipeline(
    prompt: Optional[str] = None,
    duration: int = 15,
    genre: Optional[str] = None,
    subgenre: Optional[str] = None,
    mode: str = "balanced",
    voice: Optional[str] = None,
    music_style: Optional[str] = None,
    caption_style: Optional[str] = None,
    theme: Optional[str] = None,
    seed: Optional[int] = None,
    run_qc: bool = True,
    animal_species: Optional[str] = None,
    visual_style: Optional[str] = None,
    activity_type: Optional[str] = None,
    is_duo: bool = False
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    start_time = time.time()
    print("=" * 65)
    print("🎬  AUTOREELSTUDIO — REELMAKER AI GENERATION ENGINE")
    print("=" * 65)

    # 1. Prompt Enhancement & Creative Storyboarding
    print(f"\n[1/6] 💡 Resolving Creative Strategy & Storyboard (Mode: {mode}, Duration: {duration}s)...")
    storyboard = PromptEnhancer.enhance(
        user_prompt=prompt,
        duration=duration,
        theme=theme,
        genre=genre,
        subgenre=subgenre,
        mode=mode,
        caption_style=caption_style,
        seed=seed,
        animal_species=animal_species,
        visual_style=visual_style,
        activity_type=activity_type,
        is_duo=is_duo
    )

    resolved_voice = storyboard["voice"] if (not voice or voice == "AUTO") else voice
    resolved_music = storyboard["music_style"] if (not music_style or music_style == "AUTO") else music_style
    resolved_caption_style = storyboard["caption_style"] if (not caption_style or caption_style == "AUTO") else caption_style

    print(f"      📌 Topic:         {storyboard['title']}")
    print(f"      🎭 Genre:         {storyboard['genre'].upper()} ({storyboard['subgenre']})")
    print(f"      🎨 Visual Style:  {storyboard['visual_approach']}")
    print(f"      ✍️ Caption Style: {resolved_caption_style.upper()}")
    print(f"      🎲 Seed:          {storyboard['seed']}")
    print(f"      📝 Script:        \"{storyboard['script'][:90]}...\"")

    # 2. Neural Voiceover Synthesis
    speech_rate = storyboard.get("speech_rate", "+0%")
    print(f"\n[2/6] 🎙️ Synthesizing Voiceover & Captions ({resolved_voice}, rate={speech_rate})...")
    voice_info = await TTSEngine.synthesize(
        text=storyboard["script"],
        voice=resolved_voice,
        rate=speech_rate
    )
    print(f"      🔊 Audio Duration: {voice_info['duration']:.2f}s")
    print(f"      ⏱️ Word Timings:   {len(voice_info['words'])} words mapped")

    # 3. Soundtrack & Attention SFX Generation
    total_reel_duration = max(voice_info["duration"] + 0.5, float(duration))
    print(f"\n[3/6] 🎵 Generating Procedural Soundtrack ({resolved_music}, {total_reel_duration:.1f}s)...")
    music_file = MusicEngine.generate_soundtrack(
        duration=total_reel_duration,
        style=resolved_music
    )
    print(f"      🎶 Music Track:    {Path(music_file).name}")

    # 4. Animated Subtitles with Modern Typography
    print(f"\n[4/6] ✍️ Building {resolved_caption_style.upper()} Typography Subtitles...")
    highlight_color = "#00FFA3" if storyboard["theme"] == "cosmic_purple" else "#FFE600"
    ass_file = SubtitleEngine.generate_ass(
        words=voice_info["words"],
        style=resolved_caption_style,
        highlight_color=highlight_color
    )
    print(f"      📜 Subtitles:      {Path(ass_file).name}")

    # 5. Full-Screen Visual Rendering & Native Master Assembly
    print(f"\n[5/6] 🎥 Assembling Full-Screen 9:16 Vertical Reel (1080x1920 @ 30fps)...")
    output_mp4 = VideoComposer.compose_reel(
        storyboard=storyboard,
        voice_info=voice_info,
        music_file=music_file,
        ass_subtitle_file=ass_file
    )

    # 6. Automated Quality Control & Anti-Repetition Logging
    print(f"\n[6/6] 🔍 Running Automated Quality Control & History Verification...")
    qc_result = {}
    if run_qc:
        qc_result = QualityControlEngine.audit_video(Path(output_mp4), storyboard=storyboard)
        status_icon = "✅" if qc_result.get("passed") else "⚠️"
        print(f"      {status_icon} QC Score:       {qc_result.get('score', 0)}/100 ({qc_result.get('overall_status')})")
        if qc_result.get("warnings"):
            for w in qc_result["warnings"]:
                print(f"      ⚠️ Warning:       {w}")
        if qc_result.get("errors"):
            for e in qc_result["errors"]:
                print(f"      ❌ Error:         {e}")

    # Record into Content History for anti-repetition tracking
    ContentHistory.record_generation(
        title=storyboard["title"],
        genre=storyboard["genre"],
        subgenre=storyboard["subgenre"],
        hook=storyboard.get("hook", ""),
        script=storyboard["script"],
        seed=storyboard["seed"],
        caption_style=resolved_caption_style,
        music_style=resolved_music,
        filename=Path(output_mp4).name
    )

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"🎉 INSTAGRAM REEL READY!")
    print(f"📁 Output Path:  {output_mp4}")
    print(f"⚡ Elapsed Time: {elapsed:.2f}s")
    print(f"📐 Specs:        1080x1920 (9:16 Vertical Full-Screen), H.264 + AAC Stereo")
    print("=" * 65)

    return output_mp4, storyboard, qc_result

def send_to_instagram_inbox(output_mp4: str, storyboard: dict, auto_publish: bool = False, dry_run: bool = False):
    import shutil
    from publishers.instagram.config import INBOX_DIR
    from publishers.instagram.metadata_linker import MetadataLinker
    from publishers.instagram.queue_manager import ReelQueueManager

    video_path = Path(output_mp4)
    target_video = INBOX_DIR / video_path.name
    shutil.copy(str(video_path), str(target_video))

    # Generate companion genre-aware metadata
    caption = MetadataLinker.generate_caption(
        title=storyboard.get("title", video_path.stem),
        genre=storyboard.get("genre", "science"),
        hook=storyboard.get("hook"),
        source=storyboard.get("source")
    )
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
    parser = argparse.ArgumentParser(description="AutoReelStudio (ReelMakerAI) — Intelligent Autonomous Instagram Reels Studio")
    parser.add_argument("-p", "--prompt", type=str, default=None, help="Custom prompt / concept (or leave empty for 1-click creative engine)")
    parser.add_argument("-d", "--duration", type=int, choices=[10, 15, 30, 60], default=15, help="Video duration in seconds")
    parser.add_argument("-g", "--genre", type=str, default=None, choices=list(GENRE_TAXONOMY.keys()), help="Creative genre")
    parser.add_argument("--subgenre", type=str, default=None, help="Specific subgenre within selected genre")
    parser.add_argument("-m", "--mode", type=str, default="balanced", choices=list(GENERATION_MODES.keys()), help="Creative generation mode")
    parser.add_argument("-c", "--caption-style", type=str, default=None, choices=["karaoke", "high_impact", "clean_minimal", "cinematic", "dynamic_phrase", "meme"], help="Subtitle typography style")
    parser.add_argument("-v", "--voice", type=str, default=None, help="Voice actor")
    parser.add_argument("--music", type=str, default=None, help="Soundtrack style")
    parser.add_argument("-t", "--theme", type=str, default=None, help="Color theme")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for 100%% reproducible creation")
    parser.add_argument("--no-qc", action="store_true", help="Skip automated quality control audit")
    parser.add_argument("--to-inbox", action="store_true", help="Queue into Instagram Reels inbox")
    parser.add_argument("--publish", action="store_true", help="Publish directly to Instagram Reels")
    parser.add_argument("--dry-run", action="store_true", help="Simulate Meta Graph API publishing in dry-run mode")
    parser.add_argument("--list-topics", action="store_true", help="List pre-built catalog topics and exit")

    # Animal Storytelling Engine Arguments
    parser.add_argument("--animal", type=str, default=None, help="Animal species (kitten, puppy, bunny, panda, capybara, duck, fox, otter, raccoon, etc.)")
    parser.add_argument("--style", type=str, default=None, choices=["photorealistic", "pixar_3d", "cartoon_2d", "anime", "stop_motion", "fantasy_world"], help="Visual filmmaking style")
    parser.add_argument("--activity", type=str, default=None, help="Human-like animal activity preset")
    parser.add_argument("--duo", action="store_true", help="Generate an unusual animal duo story (e.g. kitten & duckling)")

    args = parser.parse_args()

    if args.list_topics:
        print("\nAvailable AutoReelStudio Catalog Topics:")
        for t in get_catalog_topics():
            print(f"  • [{t['genre'].upper()}] {t['title']} ({t.get('subgenre')})")
        return

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

if __name__ == "__main__":
    main()
