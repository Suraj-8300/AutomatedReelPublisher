import os
import re
import urllib.request
import urllib.parse
import subprocess
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from .config import CACHE_DIR, WIDTH, HEIGHT, FPS

STOCK_DIR = CACHE_DIR / "stock_videos"
STOCK_DIR.mkdir(parents=True, exist_ok=True)

# Comprehensive keyword mapping for instant high-relevance fallbacks
SYNONYM_MAP = {
    "money": ["money", "currency", "cash", "bank", "wealth"],
    "wealth": ["money", "luxury", "city", "gold", "skyscraper"],
    "rich": ["luxury", "money", "skyscraper", "expensive", "car"],
    "billionaire": ["businessman", "skyscraper", "office", "luxury", "money"],
    "psychology": ["thinking", "mind", "brain", "people", "talking"],
    "brain": ["thinking", "laboratory", "science", "medical", "technology"],
    "mind": ["thinking", "meditation", "brain", "people", "abstract"],
    "sleep": ["sleeping", "night", "dark", "bed", "dream"],
    "ancient": ["ancient", "architecture", "stone", "ruins", "history"],
    "rome": ["ancient", "architecture", "monument", "stone", "italy"],
    "egypt": ["ancient", "pyramid", "desert", "ruins", "stone"],
    "space": ["space", "galaxy", "stars", "cosmos", "earth"],
    "galaxy": ["space", "stars", "cosmos", "nebula", "universe"],
    "black-hole": ["space", "galaxy", "stars", "dark", "cosmos"],
    "astronaut": ["space", "astronaut", "earth", "galaxy", "stars"],
    "ai": ["digital", "technology", "circuit", "robot", "neon"],
    "quantum": ["technology", "digital", "abstract", "science", "circuit"],
    "robot": ["technology", "robot", "digital", "future", "circuit"],
    "technology": ["technology", "digital", "neon", "computer", "future"],
    "nature": ["nature", "forest", "trees", "water", "landscape"],
    "ocean": ["ocean", "underwater", "water", "sea", "waves"],
    "shark": ["shark", "underwater", "ocean", "sea", "marine"],
    "forest": ["forest", "trees", "nature", "wood", "leaves"],
    "fitness": ["fitness", "gym", "workout", "athlete", "running"],
    "cold": ["ice", "winter", "water", "cold", "snow"],
    "fire": ["fire", "flame", "smoke", "burning", "sparks"],
    "city": ["city", "skyline", "skyscraper", "traffic", "urban"],
    "thinking": ["thinking", "person", "study", "work", "people"]
}

class BRollEngine:
    """
    High-performance multi-threaded B-Roll search, download,
    and video processing engine.
    """

    _session_cache: Dict[str, str] = {}

    @staticmethod
    def _search_mixkit(keyword: str) -> Optional[str]:
        clean = keyword.lower().replace(" ", "-")
        url = f"https://mixkit.co/free-stock-video/{urllib.parse.quote(clean)}/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-(?:720|1080)\.mp4', html)
                if matches:
                    return matches[0]
                matches_360 = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-\d+\.mp4', html)
                if matches_360:
                    return matches_360[0]
        except Exception:
            pass
        return None

    @staticmethod
    def _search_coverr(keyword: str) -> Optional[str]:
        clean = keyword.lower().replace(" ", "-")
        url = f"https://coverr.co/s?q={urllib.parse.quote(clean)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'https://cdn\.coverr\.co/videos/[^"]*\.mp4', html)
                if matches:
                    return matches[0]
        except Exception:
            pass
        return None

    @staticmethod
    def find_clip_for_keywords(keywords: List[str]) -> str:
        """Finds matching video URL with fast synonym cascade."""
        cache_key = "_".join(sorted(keywords))
        if cache_key in BRollEngine._session_cache:
            return BRollEngine._session_cache[cache_key]

        candidates = list(keywords)
        for kw in keywords:
            kw_clean = kw.lower().strip()
            if kw_clean in SYNONYM_MAP:
                candidates.extend(SYNONYM_MAP[kw_clean])
            for k, syns in SYNONYM_MAP.items():
                if k in kw_clean:
                    candidates.extend(syns)

        # Remove duplicates while preserving order
        unique_candidates = list(dict.fromkeys(candidates))

        for cand in unique_candidates:
            # 1. Try Mixkit
            clip = BRollEngine._search_mixkit(cand)
            if clip:
                BRollEngine._session_cache[cache_key] = clip
                return clip
            # 2. Try Coverr
            clip = BRollEngine._search_coverr(cand)
            if clip:
                BRollEngine._session_cache[cache_key] = clip
                return clip

        fallback = "https://assets.mixkit.co/videos/18791/18791-720.mp4" # Space/Cosmos universal B-roll
        BRollEngine._session_cache[cache_key] = fallback
        return fallback

    @staticmethod
    def _generate_fallback_clip(output_file: Path) -> str:
        """Procedurally creates a clean 1080x1920 abstract motion background if offline."""
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"testsrc2=s={WIDTH}x{HEIGHT}:d=5:r={FPS}",
            "-vf", "hue=s=0.2,eq=brightness=-0.3:contrast=1.2",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            str(output_file)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(output_file)

    @staticmethod
    def download_clip(url: str) -> str:
        """Fast multi-threaded downloader with disk caching and failure resilience."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        cached_file = STOCK_DIR / f"clip_{url_hash}.mp4"
        if cached_file.exists() and cached_file.stat().st_size > 50000:
            return str(cached_file)

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp, open(cached_file, "wb") as out:
                out.write(resp.read())
            return str(cached_file)
        except Exception as e:
            # Clean up partial broken download
            if cached_file.exists() and cached_file.stat().st_size < 50000:
                try:
                    cached_file.unlink()
                except OSError:
                    pass

            # Fall back to any healthy existing cached clip
            existing = [f for f in STOCK_DIR.glob("*.mp4") if f.stat().st_size > 50000]
            if existing:
                return str(existing[0])

            # Or generate procedural emergency clip
            emergency_file = STOCK_DIR / "clip_fallback_emergency.mp4"
            if not emergency_file.exists():
                BRollEngine._generate_fallback_clip(emergency_file)
            return str(emergency_file)

    @staticmethod
    def fetch_all_scene_clips_parallel(scenes: List[Dict[str, Any]]) -> List[str]:
        """
        Concurrently searches and downloads B-Roll clips for all scenes in parallel,
        reducing total retrieval time to a fraction of serial execution.
        """
        kw_lists = [s.get("keywords", ["technology", "city"]) for s in scenes]

        # Parallel search queries
        with ThreadPoolExecutor(max_workers=max(1, min(6, len(scenes)))) as executor:
            urls = list(executor.map(BRollEngine.find_clip_for_keywords, kw_lists))
            downloaded_paths = list(executor.map(BRollEngine.download_clip, urls))

        return downloaded_paths

    @staticmethod
    def process_scene_clip(
        video_path: str,
        duration: float,
        output_path: Path
    ) -> str:
        """
        Formats source clip to 9:16 vertical 1080x1920 with high-contrast color grading.
        Safe against any input aspect ratio (landscape, portrait, ultra-wide, or narrow).
        """
        vf_filter = (
            f"scale=w={WIDTH}:h={HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT}:(in_w-{WIDTH})/2:(in_h-{HEIGHT})/2,"
            f"setsar=1,fps={FPS},"
            f"eq=contrast=1.08:brightness=-0.03:saturation=1.12"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(video_path),
            "-vf", vf_filter,
            "-t", f"{duration:.2f}",
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-threads", "0",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(output_path)
