"""
Video Generation Orchestrator for AutoReelStudio.
Executes the full AI synthesis pipeline:
Quota Check (10/day limit) -> Voiceover -> AI Visuals & Camera Motion -> Ducked Soundtrack -> Dynamic Typography -> Master Composition.
"""

import os
import re
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from .quota_governor import QuotaGovernor
from .voice_engine import NaturalVoiceEngine
from .ai_visual_engine import AIVisualEngine
from .audio_master import AudioMaster
from .subtitle_engine import SubtitleEngine
from .composer import VideoComposer

class VideoGenerator:
    """Orchestrates end-to-end video synthesis from a creative idea blueprint."""

    @classmethod
    async def generate_reel(
        cls,
        idea: Dict[str, Any],
        voice_override: Optional[str] = None,
        music_override: Optional[str] = None,
        caption_override: Optional[str] = None
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Synthesizes a complete high-retention 9:16 vertical Reel.
        Checks and records against the 50 reels/day quota.
        """
        # 1. Enforce Daily 10-Reel Safety Quota
        allowed, remaining, msg = QuotaGovernor.can_generate()
        if not allowed:
            raise PermissionError(msg)

        start_time = time.time()
        title = idea.get("title", "Autonomous_Reel")
        clean_slug = re.sub(r"[^a-zA-Z0-9_]", "", title.replace(" ", "_"))[:26]
        output_filename = f"{clean_slug}_{idea.get('id', 'reel')[:6]}.mp4"

        print("=" * 65)
        print("🎬 AUTOREELSTUDIO — AI VIDEO GENERATION ENGINE")
        print("=" * 65)
        print(f"📌 Topic:         {title}")
        print(f"🎭 Genre:         {idea.get('genre', 'curiosity').upper()}")
        print(f"✍️ Hook:          \"{idea.get('hook', '')[:70]}...\"")
        print(f"📊 Daily Quota:   {remaining} remaining for today")

        # 2. Voiceover & Word Timings
        voice = voice_override or idea.get("suggested_voice", "en-US-ChristopherNeural")
        script = idea.get("script", "")
        print(f"\n[1/5] 🎙️ Synthesizing Natural Voiceover ({voice})...")
        voice_path, words_timing, total_duration = await NaturalVoiceEngine.synthesize_speech(
            text=script,
            voice=voice
        )
        print(f"      🔊 Audio Duration: {total_duration:.2f}s | Words: {len(words_timing)}")

        # 3. AI Visuals & Cinematic Motion
        scenes = idea.get("scenes", [])
        if not scenes:
            scenes = [{"text": script, "visual_prompt": f"Cinematic shot of {title}, 8k, photorealistic", "motion": "zoom_in"}]

        scene_duration = total_duration / len(scenes)
        scene_clips = []
        print(f"\n[2/5] 🎨 Generating {len(scenes)} AI Visual Scenes & Camera Motion...")
        for idx, scene in enumerate(scenes, 1):
            prompt = scene.get("visual_prompt", f"{title}, cinematic 8k vertical")
            motion = scene.get("motion", "zoom_in")
            print(f"      🖼️ Scene {idx}/{len(scenes)}: Rendering AI visual...")
            image_path = AIVisualEngine.generate_scene_image(prompt=prompt)
            print(f"      🎥 Scene {idx}/{len(scenes)}: Animating camera motion ({motion}, {scene_duration:.2f}s)...")
            clip_path = AIVisualEngine.render_motion_clip(
                image_path=image_path,
                duration=scene_duration,
                motion_type=motion
            )
            scene_clips.append(clip_path)

        # 4. Soundtrack & Audio Ducking
        music_style = music_override or idea.get("suggested_music", "cyber_pulse")
        print(f"\n[3/5] 🎵 Generating Soundtrack & Ducking Audio ({music_style})...")
        music_bed = AudioMaster.generate_music_bed(style=music_style, duration_sec=total_duration + 2.0)
        master_audio = AudioMaster.mix_and_duck_audio(
            voice_path=voice_path,
            music_path=music_bed,
            total_duration=total_duration
        )

        # 5. Dynamic ASS Subtitles
        caption_style = caption_override or idea.get("caption_style", "karaoke")
        print(f"\n[4/5] ✍️ Building Dynamic Safe-Zone Subtitles ({caption_style.upper()})...")
        subtitles_path = SubtitleEngine.generate_ass(words_timing, style=caption_style)

        # 6. Video Composition
        print(f"\n[5/5] 🎥 Assembling Full-Screen 9:16 Video (1080x1920 @ 30fps)...")
        master_video_path = VideoComposer.assemble_reel(
            scene_clips=scene_clips,
            master_audio_path=master_audio,
            subtitles_path=subtitles_path,
            output_filename=output_filename,
            total_duration=total_duration
        )

        # Record quota consumption
        new_count = QuotaGovernor.record_generation()
        elapsed = time.time() - start_time

        telemetry = {
            "title": title,
            "filename": output_filename,
            "path": str(master_video_path),
            "duration": total_duration,
            "scenes_count": len(scenes),
            "voice": voice,
            "caption_style": caption_style,
            "daily_quota_used": new_count,
            "daily_quota_limit": 10,
            "elapsed_seconds": round(elapsed, 2)
        }

        print("=" * 65)
        print(f"🎉 MASTER VIDEO GENERATED: {master_video_path.name}")
        print(f"⚡ Time Elapsed: {elapsed:.2f}s | Daily Count: {new_count}/10")
        print("=" * 65)

        return master_video_path, telemetry

