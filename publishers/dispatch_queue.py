"""
Publishing Dispatch Queue & Pacing Scheduler for AutoReelStudio.
Manages ready-to-publish videos with scheduled pacing (5 hours / 300m intervals)
and supports instant 1-click "Upload Now" bypass.
Coordinates publication across Instagram Reels and YouTube Shorts within platform safety quotas.
"""

import os
import sys
import json
import time
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_FILE = DATA_DIR / "publishing_queue.json"

from publishers.instagram.config import INBOX_DIR
from publishers.instagram.queue_manager import ReelQueueManager as InstagramQueueManager
from publishers.youtube.auth import YouTubeAuthenticator
from publishers.youtube.publisher import YouTubePublisher

DEFAULT_INTERVAL_MINUTES = 300.0 # Paced release every 300 minutes (5.0 hours)

class PublishingQueueManager:
    """Manages the queue of ready-to-publish videos and scheduled distribution."""

    @classmethod
    def _load_data(cls) -> List[Dict[str, Any]]:
        """Loads queue entries from disk."""
        if not QUEUE_FILE.exists():
            return []
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def _save_data(cls, items: List[Dict[str, Any]]):
        """Atomically saves queue entries to disk."""
        tmp = QUEUE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        tmp.replace(QUEUE_FILE)

    @classmethod
    def enqueue(
        cls,
        video_path: Path,
        title: str,
        platforms: Optional[List[str]] = None,
        instagram_meta: Optional[Dict[str, Any]] = None,
        youtube_meta: Optional[Dict[str, Any]] = None,
        scheduled_time: Optional[str] = None,
        interval_minutes: float = DEFAULT_INTERVAL_MINUTES
    ) -> Dict[str, Any]:
        """
        Adds a generated, CDN-ready video to the publishing queue.
        Calculates scheduled release time to maintain paced distribution.
        """
        items = cls._load_data()
        video_path = Path(video_path).resolve()
        now = datetime.now(timezone.utc)

        # Calculate scheduled time if not explicitly provided
        if scheduled_time:
            sched_dt = datetime.fromisoformat(scheduled_time)
        else:
            # Find the latest scheduled time among pending items
            pending = [
                datetime.fromisoformat(i["scheduled_time"])
                for i in items
                if i.get("status") in ["scheduled", "pending"] and "scheduled_time" in i
            ]
            if pending:
                latest = max(pending)
                sched_dt = max(latest + timedelta(minutes=interval_minutes), now + timedelta(minutes=interval_minutes))
            else:
                sched_dt = now + timedelta(minutes=interval_minutes)

        item_id = f"pub_{uuid.uuid4().hex[:10]}"
        platforms = platforms or ["instagram", "youtube"]

        entry = {
            "id": item_id,
            "title": title,
            "video_path": str(video_path),
            "filename": video_path.name,
            "platforms": platforms,
            "status": "scheduled", # scheduled | publishing | published | failed
            "created_at": now.isoformat(),
            "scheduled_time": sched_dt.isoformat(),
            "published_at": None,
            "instagram_meta": instagram_meta or {"caption": title},
            "youtube_meta": youtube_meta or {"title": title, "description": "", "tags": []},
            "receipts": {},
            "errors": {}
        }

        items.append(entry)
        cls._save_data(items)
        return entry

    @classmethod
    def get_queue(cls, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns the current list of queue entries, optionally filtered by status."""
        items = cls._load_data()
        if status_filter:
            return [i for i in items if i.get("status") == status_filter]
        return items

    @classmethod
    def get_item(cls, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a specific queued item by ID."""
        for item in cls._load_data():
            if item.get("id") == item_id:
                return item
        return None

    @classmethod
    def publish_now(cls, item_id: str, dry_run: bool = False, is_manual: bool = True) -> Dict[str, Any]:
        """
        Instant One-Click Upload Now (or automated scheduled dispatch):
        Bypasses scheduled timer (or executes scheduled timer).
        Enforces daily quotas:
          - Automated publish capped at 10/day (safe boundary for YouTube & Instagram).
          - Manual 1-click override allows pushing limit within the 10/day ceiling,
            and halts auto-publishing for the remainder of that day.
        """
        from video_generation.quota_governor import QuotaGovernor

        # Enforce quota safety rules
        if is_manual:
            can_pub, remaining_m, q_msg = QuotaGovernor.can_manual_publish()
            if not can_pub:
                print(f"⛔ [PublishingQueue] Manual publish rejected: {q_msg}")
                return {"success": False, "error": q_msg}
        else:
            auto_allowed, q_msg = QuotaGovernor.is_auto_publish_allowed()
            if not auto_allowed:
                print(f"⛔ [PublishingQueue] Auto publish rejected: {q_msg}")
                return {"success": False, "error": q_msg}

        items = cls._load_data()
        target_idx = None
        for idx, item in enumerate(items):
            if item.get("id") == item_id:
                target_idx = idx
                break

        if target_idx is None:
            return {"success": False, "error": f"Item {item_id} not found in publishing queue"}

        item = items[target_idx]
        item["status"] = "publishing"
        cls._save_data(items)

        video_path = Path(item["video_path"])
        if not video_path.exists():
            item["status"] = "failed"
            item["errors"]["general"] = f"Video file not found: {video_path}"
            cls._save_data(items)
            return {"success": False, "error": f"Video file not found: {video_path}"}

        platforms = item.get("platforms", ["instagram", "youtube"])
        receipts = {}
        errors = {}
        overall_success = True

        tag_str = "1-CLICK MANUAL OVERRIDE" if is_manual else "AUTOMATED SCHEDULED RELEASE"
        print("=" * 65)
        print(f"🚀 [PublishingQueue] {tag_str}: {item['title']}")
        print(f"📁 Video:     {item['filename']}")
        print(f"🎯 Targets:   {', '.join(platforms).upper()}")
        print("=" * 65)

        # 1. Instagram Reels Publish
        if "instagram" in platforms:
            try:
                print("\n📸 [PublishingQueue] Publishing to Instagram Reels...")
                INBOX_DIR.mkdir(parents=True, exist_ok=True)
                target_inbox_video = INBOX_DIR / video_path.name
                shutil.copy(str(video_path), str(target_inbox_video))

                # Write caption text companion
                caption_text = item.get("instagram_meta", {}).get("caption", item["title"])
                caption_file = INBOX_DIR / f"{video_path.stem}.txt"
                with open(caption_file, "w", encoding="utf-8") as f:
                    f.write(caption_text)

                manager = InstagramQueueManager()
                ig_result = manager.process_video_file(target_inbox_video, dry_run=dry_run)
                if ig_result.get("success"):
                    receipts["instagram"] = ig_result.get("receipt", {})
                    print(f"✅ Instagram Success: {receipts['instagram'].get('instagram_permalink')}")
                else:
                    errors["instagram"] = ig_result.get("error", "Instagram publish failed")
                    overall_success = False
                    print(f"❌ Instagram Error: {errors['instagram']}")
            except Exception as e:
                errors["instagram"] = str(e)
                overall_success = False
                print(f"❌ Instagram Exception: {e}")

        # 2. YouTube Shorts Publish
        if "youtube" in platforms:
            try:
                print("\n▶️ [PublishingQueue] Publishing to YouTube Shorts...")
                if not YouTubeAuthenticator.is_authenticated():
                    errors["youtube"] = "YouTube not authenticated. Run 'python3 autoreel.py auth-youtube' to connect."
                    overall_success = False
                    print(f"⚠️ YouTube Auth Warning: {errors['youtube']}")
                else:
                    pub = YouTubePublisher()
                    yt_meta = item.get("youtube_meta", {})
                    yt_title = yt_meta.get("title", item["title"])
                    yt_desc = yt_meta.get("description", "")
                    yt_tags = yt_meta.get("tags", [])
                    privacy = "private" if dry_run else "public"

                    yt_result = pub.upload_short(
                        video_path=video_path,
                        title=yt_title,
                        description=yt_desc,
                        tags=yt_tags,
                        privacy_status=privacy
                    )
                    if yt_result.get("success"):
                        receipts["youtube"] = yt_result
                        print(f"✅ YouTube Success: {yt_result.get('shorts_url')}")
                    else:
                        errors["youtube"] = yt_result.get("error", "YouTube upload failed")
                        overall_success = False
                        print(f"❌ YouTube Error: {errors['youtube']}")
            except Exception as e:
                errors["youtube"] = str(e)
                overall_success = False
                print(f"❌ YouTube Exception: {e}")

        # Finalize status
        item["receipts"] = receipts
        item["errors"] = errors
        item["status"] = "published" if overall_success else ("failed" if not receipts else "partially_published")
        item["published_at"] = datetime.now(timezone.utc).isoformat()

        if receipts:
            # Successfully published: remove from queue and add to rolling recently published (last 10)
            items.pop(target_idx)
            cls._save_data(items)
            from .recent_manager import RecentlyPublishedManager
            RecentlyPublishedManager.record_published(item)

            # Record in daily quota governor (triggers auto-publish stop if is_manual=True)
            from video_generation.quota_governor import QuotaGovernor
            QuotaGovernor.record_publish(is_manual=is_manual)

            mode_desc = "Manual Override (Auto-publish stopped for today)" if is_manual else "Automated Scheduled Release"
            print(f"📦 [PublishingQueue] [{mode_desc}] Removed '{item['title']}' from ready queue & added to Recently Published (rolling 10 limit).")
        else:
            # Failed to publish to any platform, retain in queue marked failed
            cls._save_data(items)

        # Build human-readable error description with smart API diagnostics
        err_msg = None
        if errors:
            formatted_errors = []
            for k, v in errors.items():
                v_str = str(v)
                if "uploadLimitExceeded" in v_str or "number of videos they may upload" in v_str:
                    formatted_errors.append("YouTube: Daily channel upload limit reached (Google 24h cap).")
                elif "API access blocked" in v_str:
                    formatted_errors.append("Instagram: Meta API access blocked. Reconnect token.")
                else:
                    formatted_errors.append(f"{k.capitalize()}: {v_str[:80]}")
            err_msg = " | ".join(formatted_errors)

        # If at least one target platform succeeded, mark as partial success so UI can update and report
        has_any_success = bool(receipts)
        is_partial = has_any_success and len(receipts) < len(platforms)

        return {
            "success": has_any_success,
            "overall_success": overall_success,
            "partial": is_partial,
            "id": item_id,
            "status": item["status"],
            "receipts": receipts,
            "errors": errors,
            "error": err_msg,
            "published_at": item["published_at"],
            "is_manual": is_manual
        }

    @classmethod
    def publish_next(cls, dry_run: bool = False, is_manual: bool = True) -> Optional[Dict[str, Any]]:
        """Publishes the earliest scheduled pending video immediately."""
        items = cls._load_data()
        pending = [
            i for i in items
            if i.get("status") in ["scheduled", "pending"]
        ]
        if not pending:
            return None
        # Sort by scheduled time
        pending.sort(key=lambda x: x.get("scheduled_time", ""))
        return cls.publish_now(pending[0]["id"], dry_run=dry_run, is_manual=is_manual)

    @classmethod
    def process_due_items(cls, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Called by the scheduler ticker.
        Checks for any scheduled items whose release time has arrived (<= now).
        Publishes them automatically if automated publishing is active today.
        """
        from video_generation.quota_governor import QuotaGovernor
        auto_allowed, reason = QuotaGovernor.is_auto_publish_allowed()
        if not auto_allowed:
            return []

        items = cls._load_data()
        now = datetime.now(timezone.utc)
        due_items = []

        for item in items:
            if item.get("status") in ["scheduled", "pending"]:
                sched_str = item.get("scheduled_time")
                if sched_str:
                    try:
                        sched_dt = datetime.fromisoformat(sched_str)
                        if sched_dt <= now:
                            due_items.append(item["id"])
                    except Exception:
                        pass

        results = []
        for item_id in due_items:
            # Double check auto quota before dispatching each item
            auto_allowed, _ = QuotaGovernor.is_auto_publish_allowed()
            if not auto_allowed:
                print("🛑 [Scheduler] Auto-publish limit or stop triggered. Halting scheduled releases.")
                break

            print(f"⏰ [Scheduler] Triggering scheduled release for due item: {item_id}")
            res = cls.publish_now(item_id, dry_run=dry_run, is_manual=False)
            results.append(res)
        return results

    @classmethod
    def cancel_item(cls, item_id: str) -> bool:
        """Cancels a scheduled queued video."""
        items = cls._load_data()
        for item in items:
            if item.get("id") == item_id:
                item["status"] = "cancelled"
                cls._save_data(items)
                return True
        return False

    @classmethod
    def remove_item(cls, item_id: str, delete_file: bool = True) -> Dict[str, Any]:
        """
        Permanently removes a reel from the publishing queue and deletes its
        master video file from disk so it frees up storage.
        """
        items = cls._load_data()
        target = None
        new_items = []
        for item in items:
            if item.get("id") == item_id:
                target = item
            else:
                new_items.append(item)

        if not target:
            return {"success": False, "error": f"Item {item_id} not found in publishing queue"}

        # Delete local video files if requested
        deleted_files = []
        if delete_file:
            vpath = target.get("video_path")
            if vpath:
                p = Path(vpath)
                if p.is_file():
                    try:
                        p.unlink()
                        deleted_files.append(str(p))
                        print(f"🗑️ [PublishingQueue] Deleted master video file: {p}")
                    except Exception as e:
                        print(f"⚠️ Could not delete video file {p}: {e}")
                # Also clean up matching jpg thumbnail if exists
                jpg_thumb = p.with_suffix(".jpg")
                if jpg_thumb.is_file():
                    try:
                        jpg_thumb.unlink()
                        deleted_files.append(str(jpg_thumb))
                    except Exception:
                        pass

        cls._save_data(new_items)
        active_remaining = len([i for i in new_items if i.get("status") in ["scheduled", "pending"]])
        print(f"🗑️ [PublishingQueue] Reel '{target.get('title')}' permanently removed from queue. Remaining: {active_remaining}")
        return {
            "success": True,
            "removed_id": item_id,
            "title": target.get("title", ""),
            "deleted_files": deleted_files,
            "remaining_count": active_remaining
        }

    @classmethod
    def clear_completed(cls) -> int:
        """Cleans up published or cancelled queue entries."""
        items = cls._load_data()
        active = [i for i in items if i.get("status") in ["scheduled", "pending", "publishing"]]
        removed = len(items) - len(active)
        cls._save_data(active)
        return removed

