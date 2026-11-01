import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import WIDTH, HEIGHT, FPS, CACHE_DIR, OUTPUT_DIR, PALETTES, FONTS
from .broll_engine import BRollEngine
from .cache_manager import CacheManager

class VideoComposer:
    """
    High-performance multi-threaded video composer.
    Assembles context-matching B-roll, voiceover, ducked music,
    pop-scale subtitles, and animated progress bars into vertical 9:16 Reels.
    """

    @staticmethod
    def compose_reel(
        storyboard: Dict[str, Any],
        voice_info: Dict[str, Any],
        music_file: str,
        ass_subtitle_file: str,
        output_file: Optional[Path] = None
    ) -> str:
        if output_file is None:
            safe_title = "".join(c for c in storyboard.get("title", "reel") if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_title = safe_title.replace(" ", "_")[:28]
            output_file = OUTPUT_DIR / f"{safe_title}_{uuid.uuid4().hex[:6]}.mp4"

        scenes = storyboard.get("scenes", [])
        palette_key = storyboard.get("theme", "cyber_blue")
        palette = PALETTES.get(palette_key, PALETTES["cyber_blue"])
        voice_audio = voice_info["audio_file"]
        total_duration = max(voice_info["duration"] + 0.4, float(storyboard.get("target_duration", 15)))

        # 1. Parallel Search & Download of All B-Roll Clips
        num_scenes = max(1, len(scenes))
        scene_duration = total_duration / num_scenes
        print(f"      ⚡ Concurrently downloading {num_scenes} matching stock video clips...")
        raw_stock_paths = BRollEngine.fetch_all_scene_clips_parallel(scenes)

        # 2. Parallel Processing & Vertical 9:16 Crop
        print(f"      🎥 Formatting clips into vertical 9:16 ({WIDTH}x{HEIGHT})...")
        scene_clip_paths = []
        process_tasks = []

        with ThreadPoolExecutor(max_workers=max(1, min(4, num_scenes))) as executor:
            for i, raw_path in enumerate(raw_stock_paths):
                out_scene_path = CACHE_DIR / f"scene_vid_{i}_{uuid.uuid4().hex[:6]}.mp4"
                scene_clip_paths.append(str(out_scene_path))
                process_tasks.append(
                    executor.submit(BRollEngine.process_scene_clip, raw_path, scene_duration, out_scene_path)
                )
            # Wait for all to finish
            for t in process_tasks:
                t.result()

        # 3. Fast Stream Concatenation
        concat_list_file = CACHE_DIR / f"concat_{uuid.uuid4().hex[:6]}.txt"
        with open(concat_list_file, "w") as f:
            for clip in scene_clip_paths:
                f.write(f"file '{clip}'\n")

        raw_video = CACHE_DIR / f"raw_video_{uuid.uuid4().hex[:6]}.mp4"
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
            "-c", "copy", str(raw_video)
        ]
        subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 4. Final Master Assembly with Multi-Track Audio Ducking & Subtitle Rendering
        accent_color_hex = palette["accent"].lstrip("#")
        raw_badge = storyboard.get("badge", "🔥 DID YOU KNOW?")
        clean_badge = (
            str(raw_badge)
            .replace("'", "")
            .replace(":", " -")
            .replace("%", "")
            .replace("\\", "")
        )

        font_path = FONTS.get("bold", "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf")
        font_arg = f"fontfile='{font_path}'" if os.path.exists(font_path) else "font='Liberation Sans'"

        filter_complex = (
            f"[0:v]"
            # Top dark gradient for branding legibility
            f"drawbox=x=0:y=0:w={WIDTH}:h=230:color=black@0.45:t=fill,"
            # Bottom dark gradient for subtitle legibility
            f"drawbox=x=0:y={HEIGHT-550}:w={WIDTH}:h=550:color=black@0.45:t=fill,"
            # Top Branding Pill Badge (Positioned at y=230, safely below the 220px Top UI Danger Zone)
            f"drawbox=x={(WIDTH-520)//2}:y=230:w=520:h=68:color=0x{palette['accent'].lstrip('#')}@0.22:t=fill,"
            f"drawbox=x={(WIDTH-520)//2}:y=230:w=520:h=68:color=0x{palette['accent'].lstrip('#')}@0.85:t=2,"
            f"drawtext=text='{clean_badge}':{font_arg}:"
            f"fontsize=28:fontcolor=0x{accent_color_hex}:x=(w-text_w)/2:y=250,"
            # Subtitle Burning
            f"ass={ass_subtitle_file},"
            # Animated bottom progress bar
            f"drawbox=x=0:y={HEIGHT-14}:w='iw*(t/{total_duration:.2f})':h=14:color=0x{accent_color_hex}@1:t=fill[vpost];"
            # Audio Mixing: voice 100% + ducked music -18dB (14% volume, longest so music smoothly finishes)
            f"[2:a]volume=0.14[bgmusic];"
            f"[1:a][bgmusic]amix=inputs=2:duration=longest:dropout_transition=2[aout]"
        )

        cmd_final = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-i", str(voice_audio),
            "-i", str(music_file),
            "-filter_complex", filter_complex,
            "-map", "[vpost]",
            "-map", "[aout]",
            "-t", str(total_duration),
            "-c:v", "libx264",
            "-profile:v", "high",
            "-preset", "ultrafast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-threads", "0",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-movflags", "+faststart",
            str(output_file)
        ]

        try:
            subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        finally:
            # Clean up all intermediate render files to avoid cache bloat
            for p in scene_clip_paths:
                try:
                    Path(p).unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                concat_list_file.unlink(missing_ok=True)
                raw_video.unlink(missing_ok=True)
            except OSError:
                pass

            # Automatically purge transient speech, music, and subtitle files
            CacheManager.clean_transient_assets(
                voice_file=str(voice_audio),
                music_file=str(music_file),
                ass_file=str(ass_subtitle_file)
            )

            # Auto-enforce global cache storage limits (LRU stock retention)
            CacheManager.auto_prune()

        return str(output_file)
