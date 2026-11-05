import os
import re
import uuid
import hashlib
import urllib.request
import urllib.parse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import CACHE_DIR, WIDTH, HEIGHT, FPS
from .broll_engine import BRollEngine
from .visual_engine import VisualEngine

ANIMAL_CACHE_DIR = CACHE_DIR / "animal_frames"
ANIMAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class AnimalVisualPipeline:
    """
    Renders cinematic, character-consistent AI visual scenes for animal & character stories.
    Fetches high-res 1080x1920 AI scene frames, applies smooth camera motion (Ken Burns),
    and formats them into full-screen 9:16 vertical clips.
    """

    @staticmethod
    def render_scene_visual(
        scene: Dict[str, Any],
        scene_index: int,
        total_scenes: int,
        seed: Optional[int] = None,
        target_scene_duration: Optional[float] = None
    ) -> str:
        """
        Renders a single scene into a vertical 1080x1920 MP4 video clip.
        Uses AI image generation with camera motion, falling back to stock clips or procedural frames.
        """
        duration = float(target_scene_duration or scene.get("duration", 5.0))
        ai_prompt = scene.get("ai_visual_prompt", "")
        clean_seed = (seed or 42) + (scene_index * 137)

        # 1. Attempt AI Scene Frame Generation
        frame_path = AnimalVisualPipeline._fetch_ai_frame(ai_prompt, clean_seed)

        # 2. Render Camera Motion on the Frame
        out_clip_path = ANIMAL_CACHE_DIR / f"scene_motion_{scene_index}_{uuid.uuid4().hex[:6]}.mp4"

        # Determine camera motion based on camera angle description
        cam_desc = scene.get("camera_angle", "").lower()
        if "push" in cam_desc or "close-up" in cam_desc:
            motion_type = "zoom_in"
        elif "pull" in cam_desc or "wide" in cam_desc:
            motion_type = "zoom_out"
        else:
            motion_type = "pan" if scene_index % 2 == 1 else "zoom_in"

        if frame_path and Path(frame_path).exists():
            try:
                VisualEngine.render_motion_scene_clip(
                    frame_path=str(frame_path),
                    duration=duration,
                    output_clip=out_clip_path,
                    motion_type=motion_type
                )
                if out_clip_path.exists() and out_clip_path.stat().st_size > 5000:
                    return str(out_clip_path)
            except Exception as e:
                print(f"[AnimalVisual] Motion render fallback for scene {scene_index}: {e}")

        # 3. Fallback to Stock Video / Procedural Clip
        try:
            keywords = scene.get("keywords", ["cute", "animal"])
            stock_url = BRollEngine.find_clip_for_keywords(keywords)
            stock_clip = BRollEngine.download_clip(stock_url)
            processed_stock = ANIMAL_CACHE_DIR / f"stock_proc_{scene_index}_{uuid.uuid4().hex[:6]}.mp4"
            BRollEngine.process_scene_clip(stock_clip, duration, processed_stock)
            if processed_stock.exists() and processed_stock.stat().st_size > 5000:
                return str(processed_stock)
        except Exception as e:
            print(f"[AnimalVisual] Stock fallback failed for scene {scene_index}: {e}")

        # 4. Ultimate Procedural Fallback
        proc_frame = VisualEngine.create_scene_frame(
            scene_info=scene,
            genre="animation",
            theme="cozy_warm"
        )
        proc_clip = ANIMAL_CACHE_DIR / f"proc_clip_{scene_index}_{uuid.uuid4().hex[:6]}.mp4"
        VisualEngine.render_motion_scene_clip(
            frame_path=proc_frame,
            duration=duration,
            output_clip=proc_clip,
            motion_type="zoom_in"
        )
        return str(proc_clip)

    @staticmethod
    def _fetch_ai_frame(prompt: str, seed: int) -> Optional[Path]:
        """Downloads high-res 1080x1920 AI scene frame from free endpoint with disk caching."""
        prompt_hash = hashlib.md5(f"{prompt}_{seed}".encode()).hexdigest()[:12]
        cached_frame = ANIMAL_CACHE_DIR / f"ai_frame_{prompt_hash}.jpg"

        if cached_frame.exists() and cached_frame.stat().st_size > 15000:
            return cached_frame

        # Truncate prompt if overly long for HTTP GET
        safe_prompt = prompt[:380]
        encoded = urllib.parse.quote(safe_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&seed={seed}&nologo=true"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoReelStudio/2.0 (ReelMakerAI)"}
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                if len(data) > 10000:
                    cached_frame.write_bytes(data)
                    return cached_frame
        except Exception as e:
            print(f"[AnimalVisual] Pollinations fetch notice: {e}")

        return None

    @staticmethod
    def render_all_scenes_parallel(
        scenes: List[Dict[str, Any]],
        seed: Optional[int] = None,
        target_scene_duration: Optional[float] = None
    ) -> List[str]:
        """Concurrently generates and renders all story scenes into vertical 9:16 video clips."""
        num_scenes = len(scenes)
        tasks = []

        with ThreadPoolExecutor(max_workers=max(1, min(4, num_scenes))) as executor:
            for idx, sc in enumerate(scenes):
                tasks.append(
                    executor.submit(
                        AnimalVisualPipeline.render_scene_visual,
                        sc,
                        idx,
                        num_scenes,
                        seed,
                        target_scene_duration
                    )
                )

        results = [t.result() for t in tasks]
        return results
