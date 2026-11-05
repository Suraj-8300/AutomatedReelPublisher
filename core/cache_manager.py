import os
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List

from .config import CACHE_DIR

STOCK_DIR = CACHE_DIR / "stock_videos"

# Defaults
DEFAULT_MAX_CACHE_MB = int(os.environ.get("MAX_CACHE_SIZE_MB", 250))
DEFAULT_MAX_AGE_HOURS = float(os.environ.get("MAX_CACHE_AGE_HOURS", 24))
DEFAULT_MAX_STOCK_MB = int(os.environ.get("MAX_STOCK_CACHE_MB", 150))

class CacheManager:
    """
    Automated Cache and Temporary Storage Garbage Collector.
    Prevents disk ballooning by enforcing LRU stock video retention,
    age-based expiration, and instant cleanup of transient render assets.
    """

    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Calculates total size and file counts in cache directory."""
        if not CACHE_DIR.exists():
            return {"total_bytes": 0, "total_mb": 0.0, "file_count": 0, "stock_count": 0}

        total_bytes = 0
        file_count = 0
        stock_count = 0

        for p in CACHE_DIR.glob("**/*"):
            if p.is_file() and p.name != ".gitkeep":
                total_bytes += p.stat().st_size
                file_count += 1
                if STOCK_DIR in p.parents or p.parent == STOCK_DIR:
                    stock_count += 1

        return {
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "file_count": file_count,
            "stock_count": stock_count
        }

    @staticmethod
    def clean_transient_assets(
        voice_file: str = None,
        music_file: str = None,
        ass_file: str = None,
        extra_paths: List[str] = None
    ) -> int:
        """Immediately removes one-off transient files produced during reel assembly."""
        deleted_bytes = 0
        targets = []
        if voice_file:
            targets.append(Path(voice_file))
        if music_file:
            targets.append(Path(music_file))
        if ass_file:
            targets.append(Path(ass_file))
        if extra_paths:
            targets.extend([Path(p) for p in extra_paths])

        for target in targets:
            try:
                if target and target.exists() and target.is_file() and target.name != ".gitkeep":
                    sz = target.stat().st_size
                    target.unlink()
                    deleted_bytes += sz
            except OSError:
                pass

        return deleted_bytes

    @staticmethod
    def auto_prune(
        max_cache_mb: int = DEFAULT_MAX_CACHE_MB,
        max_stock_mb: int = DEFAULT_MAX_STOCK_MB,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS
    ) -> Dict[str, Any]:
        """
        Runs comprehensive garbage collection:
        1. Deletes dangling transient files (raw_video_*, scene_vid_*, concat_*, music_*, voice_*, etc.).
        2. Deletes any cached file older than max_age_hours.
        3. Enforces LRU quota on stock_videos/ so it stays below max_stock_mb.
        4. Enforces global cache quota so total cache stays below max_cache_mb.
        """
        now = time.time()
        max_age_secs = max_age_hours * 3600
        deleted_count = 0
        freed_bytes = 0

        if not CACHE_DIR.exists():
            return {"freed_bytes": 0, "freed_mb": 0.0, "deleted_count": 0}

        # 1. Clean dangling top-level transient files
        transient_patterns = [
            "scene_vid_*.mp4", "raw_video_*.mp4", "concat_*.txt",
            "voice_*.mp3", "music_*.wav", "subtitles_*.ass",
            "clip_0_*.mp4", "clip_1_*.mp4", "clip_2_*.mp4", "clip_3_*.mp4", "clip_4_*.mp4",
            "frame_*.png", "safe_zone_*.jpg"
        ]
        for pattern in transient_patterns:
            for f in CACHE_DIR.glob(pattern):
                try:
                    if f.is_file() and f.name != ".gitkeep":
                        sz = f.stat().st_size
                        f.unlink()
                        freed_bytes += sz
                        deleted_count += 1
                except OSError:
                    pass

        # 2. Age-based expiration for all cache files
        for f in CACHE_DIR.glob("**/*"):
            if f.is_file() and f.name != ".gitkeep":
                try:
                    mtime = f.stat().st_mtime
                    if (now - mtime) > max_age_secs:
                        sz = f.stat().st_size
                        f.unlink()
                        freed_bytes += sz
                        deleted_count += 1
                except OSError:
                    pass

        # 3. LRU Stock Videos Quota Enforcement
        if STOCK_DIR.exists():
            stock_files = [f for f in STOCK_DIR.glob("*.mp4") if f.is_file() and f.name != ".gitkeep"]
            stock_bytes = sum(f.stat().st_size for f in stock_files)
            max_stock_bytes = max_stock_mb * 1024 * 1024

            if stock_bytes > max_stock_bytes:
                # Sort by access/modification time (oldest first)
                stock_files.sort(key=lambda x: x.stat().st_mtime)
                for sf in stock_files:
                    if stock_bytes <= (max_stock_bytes * 0.75):  # prune down to 75%
                        break
                    try:
                        sz = sf.stat().st_size
                        sf.unlink()
                        stock_bytes -= sz
                        freed_bytes += sz
                        deleted_count += 1
                    except OSError:
                        pass

        # 4. Global Cache Size Quota Enforcement
        all_cache_files = [f for f in CACHE_DIR.glob("**/*") if f.is_file() and f.name != ".gitkeep"]
        total_cache_bytes = sum(f.stat().st_size for f in all_cache_files)
        max_cache_bytes = max_cache_mb * 1024 * 1024

        if total_cache_bytes > max_cache_bytes:
            all_cache_files.sort(key=lambda x: x.stat().st_mtime)
            for cf in all_cache_files:
                if total_cache_bytes <= (max_cache_bytes * 0.6):  # prune down to 60%
                    break
                try:
                    sz = cf.stat().st_size
                    cf.unlink()
                    total_cache_bytes -= sz
                    freed_bytes += sz
                    deleted_count += 1
                except OSError:
                    pass

        return {
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "deleted_count": deleted_count
        }

    @staticmethod
    def purge_all(keep_stock_clips: int = 5) -> Dict[str, Any]:
        """
        Total deep clean: Removes all transient files and prunes stock videos
        down to only the top N most recent clips.
        """
        freed_bytes = 0
        deleted_count = 0

        if not CACHE_DIR.exists():
            return {"freed_bytes": 0, "freed_mb": 0.0, "deleted_count": 0}

        # Delete all files directly under CACHE_DIR except .gitkeep
        for f in CACHE_DIR.iterdir():
            if f.is_file() and f.name != ".gitkeep":
                try:
                    sz = f.stat().st_size
                    f.unlink()
                    freed_bytes += sz
                    deleted_count += 1
                except OSError:
                    pass

        # Prune stock videos
        if STOCK_DIR.exists():
            stock_files = sorted(
                [f for f in STOCK_DIR.glob("*.mp4") if f.is_file() and f.name != ".gitkeep"],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            # Remove everything beyond keep_stock_clips
            for old_clip in stock_files[keep_stock_clips:]:
                try:
                    sz = old_clip.stat().st_size
                    old_clip.unlink()
                    freed_bytes += sz
                    deleted_count += 1
                except OSError:
                    pass

        return {
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "deleted_count": deleted_count
        }

