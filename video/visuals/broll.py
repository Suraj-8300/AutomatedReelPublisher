"""
B-Roll Video Engine for AutoReelStudio.
Sources authentic, high-definition live-action MP4 video footage from open stock repositories
(Mixkit, Coverr) with keyword expansion, disk caching, and parallel processing.
Formats raw clips into 1080x1920 9:16 vertical video with filmic color grading.
"""

import os
import re
import urllib.request
import urllib.parse
import subprocess
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from video.config import (
    CACHE_DIR, TARGET_WIDTH, TARGET_HEIGHT, TARGET_FPS,
    VIDEO_CRF, VIDEO_PRESET
)

STOCK_DIR = CACHE_DIR / "stock_videos"
STOCK_DIR.mkdir(parents=True, exist_ok=True)

# Comprehensive keyword mapping for multi-genre B-roll retrieval
SYNONYM_MAP = {
    # Animals & Cute Pets
    "kitten": ["kitten", "cat", "sleeping cat", "kitten playing", "cute animal", "pet"],
    "cat": ["cat", "kitten", "sleeping cat", "petting cat", "pet"],
    "cats": ["cat", "kitten", "pet"],
    "puppy": ["puppy", "dog", "puppy playing", "dog running", "pet"],
    "dog": ["dog", "puppy", "petting dog", "dog running", "pet"],
    "dogs": ["dog", "puppy", "pet"],
    "pet": ["puppy", "kitten", "dog", "cat"],
    "animal": ["puppy", "kitten", "dog", "cat", "nature"],
    "rescue": ["petting dog", "petting cat", "dog", "cat", "friendship"],
    "duckling": ["duck", "birds", "water", "nature"],
    "owl": ["bird", "nature", "forest"],
    "fawn": ["deer", "nature", "forest"],
    "baby animal": ["puppy", "kitten", "cute animal"],

    # Actions bound to pets / humans
    "petting": ["petting dog", "petting cat", "dog", "cat"],
    "feeding": ["feeding dog", "feeding cat", "cat eating", "dog eating"],
    "holding": ["petting dog", "petting cat", "hug", "friends"],
    "cuddle": ["dog cuddle", "cat cuddle", "sleeping cat", "pet"],
    "playing": ["puppy playing", "kitten playing", "dog running", "happy"],
    "running": ["dog running", "running", "park", "nature"],
    "shivering": ["rain", "cold", "winter", "kitten"],
    "alone": ["rain window", "night", "dark", "dog"],
    "scared": ["rain", "window", "dog", "cat"],
    "hands": ["petting dog", "petting cat", "hand", "touch"],

    # Story Settings & Human Activities
    "rain": ["rain", "rain window", "water drops", "storm"],
    "cold": ["winter", "snow", "rain", "window"],
    "winter": ["snow", "winter", "cold"],
    "snow": ["snow", "winter", "cold"],
    "baker": ["baking", "kitchen", "bread", "cooking"],
    "bakery": ["baking", "bread", "kitchen", "coffee"],
    "kitchen": ["kitchen", "cooking", "food", "warm"],
    "cooking": ["cooking", "kitchen", "food"],
    "bread": ["baking", "bread", "kitchen"],
    "warmth": ["fireplace", "fire", "cozy", "kitchen"],
    "fireplace": ["fire", "fireplace", "warm"],
    "cozy": ["cozy", "coffee", "sleeping", "living room"],
    "sleeping": ["sleeping cat", "sleeping dog", "bed", "rest"],
    "friendship": ["friends", "hug", "happy", "smile"],
    "love": ["heart", "friends", "happy", "smile"],
    "happy": ["happy", "smile", "laugh", "sunshine"],

    # Nature & Ocean
    "forest": ["forest", "trees", "nature"],
    "trees": ["forest", "nature", "trees"],
    "nature": ["nature", "forest", "clouds", "sunshine"],
    "sunshine": ["sunlight", "sun", "nature", "sky"],
    "sun": ["sun", "sunset", "sky"],
    "sunset": ["sunset", "sky", "clouds"],
    "ocean": ["ocean", "waves", "underwater", "water"],
    "sea": ["ocean", "waves", "water"],
    "waves": ["waves", "ocean", "water"],
    "underwater": ["underwater", "ocean", "fish"],
    "water": ["water", "stream", "lake", "ocean"],

    # Science & Space & Tech
    "space": ["space", "stars", "galaxy", "earth"],
    "cosmos": ["space", "stars", "universe"],
    "stars": ["stars", "space", "night sky"],
    "galaxy": ["space", "stars", "galaxy"],
    "earth": ["earth", "space", "globe"],
    "science": ["laboratory", "microscope", "science", "technology"],
    "laboratory": ["laboratory", "science", "chemistry"],
    "microscope": ["microscope", "laboratory", "science"],
    "technology": ["technology", "computer", "digital", "code"],
    "computer": ["computer", "code", "laptop", "screen"],
    "code": ["code", "computer", "programming"],
    "machine": ["machine", "gears", "factory", "technology"],
    "gears": ["gears", "clockwork", "technology", "machine"],
    "engine": ["engine", "car", "mechanic", "machine"],
    "city": ["city", "street", "buildings", "urban"],
    "traffic": ["city", "traffic", "cars"],
}

DEFAULT_FALLBACK_CLIPS = [
    "https://assets.mixkit.co/videos/26370/26370-720.mp4",  # Cute orange kitten
    "https://assets.mixkit.co/videos/1779/1779-1080.mp4",   # Domestic cat
    "https://assets.mixkit.co/videos/1479/1479-1080.mp4",   # Golden retriever dog
    "https://assets.mixkit.co/videos/2213/2213-1080.mp4",   # Lush green forest nature
    "https://assets.mixkit.co/videos/48525/48525-720.mp4",  # Ocean waves
    "https://assets.mixkit.co/videos/18791/18791-720.mp4",  # Stars in deep space
]


class BRollEngine:
    """
    Intelligent Live-Action Stock Video B-Roll Engine.
    Discovers, downloads, and formats high-definition video clips matching story scenes.
    """

    _session_cache: Dict[str, str] = {}
    _browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }

    @classmethod
    def _search_mixkit(cls, keyword: str) -> List[str]:
        """Searches Mixkit for free commercial HD stock video clips."""
        clean = keyword.lower().strip().replace(" ", "-")
        url = f"https://mixkit.co/free-stock-video/{urllib.parse.quote(clean)}/"
        req = urllib.request.Request(url, headers=cls._browser_headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-(?:720|1080)\.mp4', html)
                if not matches:
                    matches = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-\d+\.mp4', html)
                return matches[:5]
        except Exception:
            return []

    @classmethod
    def _search_coverr(cls, keyword: str) -> List[str]:
        """Searches Coverr for free commercial stock video clips."""
        clean = keyword.lower().strip().replace(" ", "-")
        url = f"https://coverr.co/s?q={urllib.parse.quote(clean)}"
        req = urllib.request.Request(url, headers=cls._browser_headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'https://cdn\.coverr\.co/videos/[^\"\'\s]+\.mp4', html)
                return matches[:5]
        except Exception:
            return []

    @classmethod
    def find_clip_url(
        cls,
        keywords: List[str],
        scene_index: int = 0,
        exclude_urls: Optional[set] = None
    ) -> str:
        """
        Finds a matching live-action video clip URL using keyword cascading.
        Filters out any URL in exclude_urls so each scene gets a distinct video.
        """
        cache_key = f"{'_'.join(sorted(keywords))}_{scene_index}"
        if cache_key in cls._session_cache and (not exclude_urls or cls._session_cache[cache_key] not in exclude_urls):
            return cls._session_cache[cache_key]

        candidates = []
        for kw in keywords:
            kw_clean = kw.lower().strip()
            candidates.append(kw_clean)
            if kw_clean in SYNONYM_MAP:
                candidates.extend(SYNONYM_MAP[kw_clean])

        unique_cands = list(dict.fromkeys(candidates))[:5]

        # 1. Search Mixkit
        for cand in unique_cands:
            matches = cls._search_mixkit(cand)
            if matches:
                available = [m for m in matches if not exclude_urls or m not in exclude_urls]
                if available:
                    selected = available[scene_index % len(available)]
                    cls._session_cache[cache_key] = selected
                    return selected

        # 2. Search Coverr
        for cand in unique_cands:
            matches = cls._search_coverr(cand)
            if matches:
                available = [m for m in matches if not exclude_urls or m not in exclude_urls]
                if available:
                    selected = available[scene_index % len(available)]
                    cls._session_cache[cache_key] = selected
                    return selected

        # 3. Default fallback
        for fb in DEFAULT_FALLBACK_CLIPS:
            if not exclude_urls or fb not in exclude_urls:
                return fb
        fallback = DEFAULT_FALLBACK_CLIPS[scene_index % len(DEFAULT_FALLBACK_CLIPS)]
        cls._session_cache[cache_key] = fallback
        return fallback

    @classmethod
    def download_clip(cls, url: str) -> Path:
        """Downloads stock clip to cache directory with failure resilience."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        cached_file = STOCK_DIR / f"clip_{url_hash}.mp4"

        if cached_file.exists() and cached_file.stat().st_size > 50000:
            return cached_file

        req = urllib.request.Request(url, headers=cls._browser_headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp, open(cached_file, "wb") as out:
                out.write(resp.read())
            return cached_file
        except Exception as e:
            # Fallback to any existing cached clip
            existing = [f for f in STOCK_DIR.glob("*.mp4") if f.stat().st_size > 50000]
            if existing:
                return existing[0]
            raise RuntimeError(f"Could not download clip from {url}: {e}")

    @classmethod
    def process_scene_clip(
        cls,
        raw_video_path: Path,
        duration: float,
        output_path: Path,
    ) -> Path:
        """
        Converts raw footage into a full-screen vertical 9:16 (1080x1920) clip.
        Applies filmic color enhancement, center cropping, and smooth looping if needed.
        """
        vf_filter = (
            f"scale=w={TARGET_WIDTH}:h={TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={TARGET_WIDTH}:{TARGET_HEIGHT}:(in_w-{TARGET_WIDTH})/2:(in_h-{TARGET_HEIGHT})/2,"
            f"setsar=1,fps={TARGET_FPS},"
            f"eq=contrast=1.06:brightness=-0.02:saturation=1.10"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(raw_video_path),
            "-vf", vf_filter,
            "-t", f"{duration:.3f}",
            "-an",
            "-c:v", "libx264",
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0 or not output_path.exists():
            # Fallback without -stream_loop
            cmd_fallback = [
                "ffmpeg", "-y",
                "-i", str(raw_video_path),
                "-vf", vf_filter,
                "-t", f"{duration:.3f}",
                "-an",
                "-c:v", "libx264",
                "-preset", VIDEO_PRESET,
                "-crf", str(VIDEO_CRF),
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
            subprocess.run(cmd_fallback, capture_output=True, check=True)

        return output_path

    @classmethod
    def fetch_and_process_scenes(
        cls,
        scenes: List[Dict[str, Any]],
        durations: List[float],
        run_id: str = "run",
    ) -> List[Path]:
        """
        Concurrently downloads and formats live-action stock video clips for all scenes.
        Returns a list of formatted 1080x1920 MP4 clips matching the scene durations.
        """
        num_scenes = len(scenes)
        print(f"  🎬 Searching and downloading {num_scenes} authentic live-action video scenes...")

        # Extract keyword lists for each scene
        scene_keywords = []
        for s in scenes:
            kws = s.get("keywords", [])
            if not kws:
                # Fallback to search_fallback or text
                fallback = s.get("search_fallback") or s.get("text", "")
                kws = [w.strip() for w in fallback.replace(",", " ").split() if len(w.strip()) > 2]
            scene_keywords.append(kws or ["nature", "life"])

        # Find unique URLs across scenes
        urls = []
        used_urls = set()
        for i in range(num_scenes):
            url = cls.find_clip_url(scene_keywords[i], scene_index=i, exclude_urls=used_urls)
            urls.append(url)
            used_urls.add(url)

        # Download raw clips in parallel
        print("  ⚡ Downloading HD video footage in parallel...")
        with ThreadPoolExecutor(max_workers=min(4, num_scenes)) as executor:
            raw_paths = list(executor.map(cls.download_clip, urls))

        # Format clips in parallel to vertical 9:16
        print("  🎥 Formatting video clips to 1080x1920 vertical with filmic color grading...")
        formatted_clips = []
        tasks = []
        with ThreadPoolExecutor(max_workers=min(4, num_scenes)) as executor:
            for i in range(num_scenes):
                dur = durations[i] if i < len(durations) else 8.0
                out_path = CACHE_DIR / f"broll_scene_{run_id}_{i}.mp4"
                formatted_clips.append(out_path)
                tasks.append(
                    executor.submit(cls.process_scene_clip, raw_paths[i], dur, out_path)
                )
            for t in tasks:
                t.result()

        return formatted_clips
