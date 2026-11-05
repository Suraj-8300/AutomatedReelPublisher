"""
Recently Published Reels Manager for AutoReelStudio.
Maintains a rolling buffer of the last 10 published reels (Instagram & YouTube).
When new reels are published, any reel before the 10th is permanently deleted from disk.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECENT_PUBLISHED_FILE = DATA_DIR / "recently_published.json"
MAX_RECENT_PUBLISHED = 10

class RecentlyPublishedManager:
    """Manages the rolling archive of the last 10 published reels."""

    @classmethod
    def _load_data(cls) -> List[Dict[str, Any]]:
        """Loads published items from disk."""
        if not RECENT_PUBLISHED_FILE.exists():
            return []
        try:
            with open(RECENT_PUBLISHED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def _save_data(cls, items: List[Dict[str, Any]]):
        """Atomically saves published items to disk."""
        tmp = RECENT_PUBLISHED_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        tmp.replace(RECENT_PUBLISHED_FILE)

    @classmethod
    def get_recent(cls, limit: int = MAX_RECENT_PUBLISHED) -> List[Dict[str, Any]]:
        """Returns the list of the last 10 published reels (newest first)."""
        items = cls._load_data()
        return items[:limit]

    @classmethod
    def record_published(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds a freshly published reel to the top of the recently published list.
        Enforces strict MAX_RECENT_PUBLISHED (10).
        Any reel pushed beyond the 10th limit is permanently deleted forever from disk.
        """
        items = cls._load_data()

        # Format record
        record = {
            "id": item.get("id"),
            "title": item.get("title", "Untitled Reel"),
            "filename": item.get("filename", Path(item.get("video_path", "")).name),
            "video_path": str(item.get("video_path", "")),
            "platforms": item.get("platforms", []),
            "published_at": item.get("published_at"),
            "receipts": item.get("receipts", {}),
            "instagram_permalink": item.get("receipts", {}).get("instagram", {}).get("instagram_permalink"),
            "youtube_shorts_url": item.get("receipts", {}).get("youtube", {}).get("shorts_url"),
            "youtube_watch_url": item.get("receipts", {}).get("youtube", {}).get("watch_url"),
            "youtube_video_id": item.get("receipts", {}).get("youtube", {}).get("video_id")
        }

        # Filter out if item already exists by ID
        items = [i for i in items if i.get("id") != record["id"]]

        # Prepend newest published item
        items.insert(0, record)

        # Enforce rolling window of 10
        if len(items) > MAX_RECENT_PUBLISHED:
            prune_items = items[MAX_RECENT_PUBLISHED:]
            items = items[:MAX_RECENT_PUBLISHED]
            for old_item in prune_items:
                deleted_files = cls._purge_reel_files(old_item)
                print(f"🗑️ [RecentlyPublished] Pruned reel beyond 10 limit: '{old_item.get('title')}' — Deleted {len(deleted_files)} files forever.")

        cls._save_data(items)
        return record

    @classmethod
    def delete_entry(cls, item_id: str, delete_files: bool = True) -> bool:
        """Manually deletes an entry from recently published and cleans up its files."""
        items = cls._load_data()
        target = None
        remaining = []
        for i in items:
            if i.get("id") == item_id:
                target = i
            else:
                remaining.append(i)

        if not target:
            return False

        if delete_files:
            cls._purge_reel_files(target)

        cls._save_data(remaining)
        return True

    @classmethod
    def _purge_reel_files(cls, item: Dict[str, Any]) -> List[str]:
        """
        Permanently deletes all video, companion, output, and archive files
        associated with a reel from disk forever.
        """
        deleted: List[str] = []
        filename = item.get("filename", "")
        vpath_str = item.get("video_path", "")
        stem = Path(filename).stem if filename else (Path(vpath_str).stem if vpath_str else "")

        if not stem:
            return deleted

        # 1. Delete main video file
        if vpath_str:
            vpath = Path(vpath_str)
            if vpath.exists():
                try:
                    vpath.unlink()
                    deleted.append(str(vpath))
                except Exception as e:
                    print(f"⚠️ Could not delete {vpath}: {e}")

            # Delete companion files next to main video (.txt, .jpg, .png, .json)
            for ext in [".txt", ".jpg", ".png", ".json"]:
                comp = vpath.with_suffix(ext)
                if comp.exists():
                    try:
                        comp.unlink()
                        deleted.append(str(comp))
                    except Exception:
                        pass

        # 2. Clean matching files from output directory
        output_dir = PROJECT_ROOT / "output"
        if output_dir.exists():
            for f in output_dir.glob(f"*{stem}*"):
                if f.is_file():
                    try:
                        f.unlink()
                        deleted.append(str(f))
                    except Exception:
                        pass

        # 3. Clean matching folders from reels_archive directory
        archive_dir = PROJECT_ROOT / "reels_archive"
        if archive_dir.exists():
            for d in archive_dir.glob(f"*{stem}*"):
                if d.is_dir():
                    try:
                        shutil.rmtree(str(d))
                        deleted.append(str(d))
                    except Exception:
                        pass
                elif d.is_file():
                    try:
                        d.unlink()
                        deleted.append(str(d))
                    except Exception:
                        pass

        # 4. Clean matching files in reels_inbox & reels_processing
        for folder_name in ["reels_inbox", "reels_processing"]:
            folder = PROJECT_ROOT / folder_name
            if folder.exists():
                for f in folder.glob(f"*{stem}*"):
                    try:
                        if f.is_dir():
                            shutil.rmtree(str(f))
                        else:
                            f.unlink()
                        deleted.append(str(f))
                    except Exception:
                        pass

        return deleted

