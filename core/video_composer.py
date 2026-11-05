import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import WIDTH, HEIGHT, FPS, CACHE_DIR, OUTPUT_DIR, PALETTES
from .broll_engine import BRollEngine
from .cache_manager import CacheManager
from .animal_visual_pipeline import AnimalVisualPipeline

class VideoComposer:
    """
    Instagram-Native High-Performance Video Composer.
    Renders pure full-screen vertical 9:16 (1080x1920) Reels without artificial borders,
    floating containers, or top title boxes.
    Handles multi-track audio ducking, subtitle burning, and Instagram-compliant H.264 encoding.
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
        voice_audio = voice_info["audio_file"]
        visual_approach = storyboard.get("visual_approach", "stock_footage")
        total_duration = max(voice_info["duration"] + 0.4, float(storyboard.get("target_duration", 15)))

        # 1 & 2: Scene Generation & Formatting
        num_scenes = max(1, len(scenes))
        scene_duration = total_duration / num_scenes
        is_animal = storyboard.get("is_animal_story", False)

        if is_animal:
            print(f"      🐾 Concurrently rendering {num_scenes} AI animal visual scenes ({storyboard.get('visual_style', 'pixar_3d')})...")
            scene_clip_paths = AnimalVisualPipeline.render_all_scenes_parallel(
                scenes=scenes,
                seed=storyboard.get("seed"),
                target_scene_duration=scene_duration
            )
        else:
            # 1. Parallel Search & Download / Generation of Scene Clips
            print(f"      ⚡ Concurrently preparing {num_scenes} visual scenes ({visual_approach})...")
            raw_scene_paths = BRollEngine.fetch_all_scene_clips_parallel(scenes, visual_approach=visual_approach)

            # 2. Format Clips into Clean Vertical 9:16 (1080x1920)
            print(f"      🎥 Formatting scenes to full-screen 9:16 ({WIDTH}x{HEIGHT})...")
            scene_clip_paths = []
            process_tasks = []

            with ThreadPoolExecutor(max_workers=max(1, min(4, num_scenes))) as executor:
                for i, raw_path in enumerate(raw_scene_paths):
                    out_scene_path = CACHE_DIR / f"scene_vid_{i}_{uuid.uuid4().hex[:6]}.mp4"
                    scene_clip_paths.append(str(out_scene_path))
                    process_tasks.append(
                        executor.submit(BRollEngine.process_scene_clip, raw_path, scene_duration, out_scene_path)
                    )
                for t in process_tasks:
                    t.result()

        # 3. Concatenate Scene Clips into Continuous Video Stream
        concat_list_file = CACHE_DIR / f"concat_{uuid.uuid4().hex[:6]}.txt"
        with open(concat_list_file, "w") as f:
            for clip in scene_clip_paths:
                f.write(f"file '{clip}'\n")

        raw_video = CACHE_DIR / f"raw_video_{uuid.uuid4().hex[:6]}.mp4"
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-r", str(FPS), str(raw_video)
        ]
        subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 4. Master Assembly: Clean Full-Screen Native Reel
        # Subtitle burning via ASS, audio ducking: voice 100% + ducked music ~14% volume (-17dB)
        # Smooth audio fade-out in final 1.5s
        fade_out_start = max(0.0, total_duration - 1.5)
        filter_complex = (
            f"[0:v]ass={ass_subtitle_file}[vpost];"
            f"[2:a]volume=0.14,afade=t=out:st={fade_out_start:.2f}:d=1.5[bgmusic];"
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
            "-crf", "21",
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
            # Clean up intermediate render files
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

            # Automatically clean transient audio and subtitle files
            CacheManager.clean_transient_assets(
                voice_file=str(voice_audio),
                music_file=str(music_file),
                ass_file=str(ass_subtitle_file)
            )

            # Auto-enforce global cache storage limits
            CacheManager.auto_prune()

        return str(output_file)
