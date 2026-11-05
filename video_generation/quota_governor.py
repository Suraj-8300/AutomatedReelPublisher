"""
Daily Quota Governor for AutoReelStudio.
Enforces the 10 reels/day safe publishing ceiling and ~2.4-hour cadence.
Protects Instagram Graph API and YouTube Data API channels against rate-limits and uploadLimitExceeded errors.
Supports 1-Click "Publish Now" manual overrides within the strict 10 reels/day ceiling,
automatically halting background auto-publishing when manual override is triggered.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUOTA_FILE = DATA_DIR / "daily_quota.json"

DAILY_AUTO_MAX = 10       # Safe automated reels per day (avoids YouTube & IG daily upload limit)
DAILY_MANUAL_MAX = 5      # Maximum manual pushes when auto-publishing is stopped
DAILY_MAX_REELS = 10      # Preserved for backward compatibility (daily target)
TOTAL_MAX_CEILING = 10    # Hard maximum limit per 24 hours across all uploads (YouTube/Meta safe boundary)

class QuotaGovernor:
    """
    Tracks and enforces daily distribution quotas:
      - 50 reels/day auto-publishing baseline.
      - 1-Click "Publish Now" allows pushing up to +20 extra reels.
      - Triggering "Publish Now" stops auto-publishing for that day.
    """

    @staticmethod
    def _today_str() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @classmethod
    def _load_data(cls) -> Dict[str, Any]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        today = cls._today_str()
        default_data = {
            "date": today,
            "count": 0,
            "auto_count": 0,
            "manual_count": 0,
            "auto_publish_stopped": False,
            "auto_publish_stopped_reason": "",
            "history": {}
        }
        if not QUOTA_FILE.exists():
            return default_data
        try:
            with open(QUOTA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") != today:
                    # Archive yesterday's count into history
                    old_date = data.get("date")
                    old_count = data.get("count", 0)
                    history = data.get("history", {})
                    if old_date:
                        history[old_date] = {
                            "total": old_count,
                            "auto": data.get("auto_count", old_count),
                            "manual": data.get("manual_count", 0),
                            "auto_stopped": data.get("auto_publish_stopped", False)
                        }
                    data = {
                        "date": today,
                        "count": 0,
                        "auto_count": 0,
                        "manual_count": 0,
                        "auto_publish_stopped": False,
                        "auto_publish_stopped_reason": "",
                        "history": history
                    }
                    cls._save_data(data)
                else:
                    # Ensure all modern keys are present
                    if "auto_count" not in data:
                        data["auto_count"] = data.get("count", 0)
                    if "manual_count" not in data:
                        data["manual_count"] = 0
                    if "auto_publish_stopped" not in data:
                        data["auto_publish_stopped"] = False
                    if "auto_publish_stopped_reason" not in data:
                        data["auto_publish_stopped_reason"] = ""
                return data
        except Exception:
            return default_data

    @classmethod
    def _save_data(cls, data: Dict[str, Any]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = QUOTA_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(QUOTA_FILE)

    @classmethod
    def is_auto_publish_allowed(cls) -> Tuple[bool, str]:
        """
        Verifies whether automated scheduled publishing is permitted today.
        Returns False if auto-publish has been stopped by manual override or reached 50.
        """
        data = cls._load_data()
        auto_count = data.get("auto_count", 0)
        auto_stopped = data.get("auto_publish_stopped", False)
        reason = data.get("auto_publish_stopped_reason", "")

        if auto_stopped:
            msg = reason or "⛔ Auto-publish is stopped for today (1-Click manual override active)."
            return False, msg

        if auto_count >= DAILY_AUTO_MAX:
            msg = f"⛔ Daily auto-publish target reached: {auto_count}/{DAILY_AUTO_MAX} reels published today."
            return False, msg

        remaining = DAILY_AUTO_MAX - auto_count
        return True, f"✅ Auto-publish active: {auto_count}/{DAILY_AUTO_MAX} published ({remaining} remaining)."

    @classmethod
    def can_manual_publish(cls) -> Tuple[bool, int, str]:
        """
        Verifies whether 1-Click 'Publish Now' manual override is allowed.
        Allows up to 20 manual reels pushed per day.
        Returns: (allowed: bool, remaining_manual: int, message: str)
        """
        data = cls._load_data()
        manual_count = data.get("manual_count", 0)
        total_count = data.get("count", 0)
        remaining = max(0, DAILY_MANUAL_MAX - manual_count)

        if manual_count >= DAILY_MANUAL_MAX:
            msg = f"⛔ Daily manual override ceiling reached: {manual_count}/{DAILY_MANUAL_MAX} manual reels pushed today."
            return False, 0, msg

        if total_count >= TOTAL_MAX_CEILING:
            msg = f"⛔ Daily total cap reached ({total_count}/{TOTAL_MAX_CEILING} reels)."
            return False, 0, msg

        msg = f"✅ Manual override permitted: {manual_count}/{DAILY_MANUAL_MAX} pushed today ({remaining} remaining)."
        return True, remaining, msg

    @classmethod
    def can_generate(cls) -> Tuple[bool, int, str]:
        """
        Checks if Reel generation is allowed today under safety caps.
        Returns: (allowed: bool, remaining_today: int, message: str)
        """
        data = cls._load_data()
        auto_count = data.get("auto_count", 0)
        manual_count = data.get("manual_count", 0)
        total_count = data.get("count", 0)
        auto_stopped = data.get("auto_publish_stopped", False)

        remaining_auto = max(0, DAILY_AUTO_MAX - auto_count)
        remaining_manual = max(0, DAILY_MANUAL_MAX - manual_count)

        if auto_stopped:
            if manual_count >= DAILY_MANUAL_MAX:
                return False, 0, f"⛔ Daily limit reached: {manual_count}/{DAILY_MANUAL_MAX} manual override reels used today."
            return True, remaining_manual, f"⚠️ Auto-publish stopped. Manual override active: {remaining_manual} remaining."

        if auto_count >= DAILY_AUTO_MAX:
            if manual_count < DAILY_MANUAL_MAX and total_count < TOTAL_MAX_CEILING:
                return True, remaining_manual, f"✅ Auto target reached (10/10). {remaining_manual} manual override reels available."
            return False, 0, f"⛔ Daily cap reached ({TOTAL_MAX_CEILING}/{TOTAL_MAX_CEILING} reels limit for YouTube & Instagram)."

        return True, remaining_auto, f"✅ Quota OK: {auto_count}/{DAILY_AUTO_MAX} generated today ({remaining_auto} remaining)."

    @classmethod
    def record_publish(cls, is_manual: bool = False) -> Dict[str, Any]:
        """
        Records a published reel:
          - If is_manual=True: increments manual_count and STOPS auto-publishing for today.
          - If is_manual=False: increments auto_count.
          - Increments total count.
        """
        data = cls._load_data()
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        if is_manual:
            data["manual_count"] = data.get("manual_count", 0) + 1
            data["auto_publish_stopped"] = True
            data["auto_publish_stopped_reason"] = (
                f"Auto-publishing stopped for today: 1-Click Manual Override triggered at {now_str} "
                f"({data['manual_count']}/{DAILY_MANUAL_MAX} manual reels used)."
            )
            print(f"🛑 [QuotaGovernor] Manual override triggered. Auto-publishing stopped for remainder of today.")
        else:
            data["auto_count"] = data.get("auto_count", 0) + 1
            if data["auto_count"] >= DAILY_AUTO_MAX:
                data["auto_publish_stopped"] = True
                data["auto_publish_stopped_reason"] = (
                    f"Daily auto-publish target reached: {data['auto_count']}/{DAILY_AUTO_MAX} reels published today."
                )
                print(f"🎯 [QuotaGovernor] Daily auto-publish target (10) completed for today.")

        data["count"] = data.get("auto_count", 0) + data.get("manual_count", 0)
        cls._save_data(data)
        return cls.get_status()

    @classmethod
    def record_generation(cls) -> int:
        """Increments today's generated count (backward compatibility)."""
        data = cls._load_data()
        data["count"] = data.get("count", 0) + 1
        cls._save_data(data)
        return data["count"]

    @classmethod
    def stop_auto_publish(cls, reason: str = "Manual override activated") -> Dict[str, Any]:
        """Manually halts auto-publishing for today."""
        data = cls._load_data()
        data["auto_publish_stopped"] = True
        data["auto_publish_stopped_reason"] = reason
        cls._save_data(data)
        return cls.get_status()

    @classmethod
    def resume_auto_publish(cls) -> Dict[str, Any]:
        """Re-enables auto-publishing for today if auto_count < 10."""
        data = cls._load_data()
        if data.get("auto_count", 0) >= DAILY_AUTO_MAX:
            return cls.get_status()
        data["auto_publish_stopped"] = False
        data["auto_publish_stopped_reason"] = ""
        cls._save_data(data)
        return cls.get_status()

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns comprehensive quota telemetry."""
        data = cls._load_data()
        auto_count = data.get("auto_count", 0)
        manual_count = data.get("manual_count", 0)
        count = data.get("count", auto_count + manual_count)
        auto_stopped = data.get("auto_publish_stopped", False)

        remaining_auto = max(0, DAILY_AUTO_MAX - auto_count)
        remaining_manual = max(0, DAILY_MANUAL_MAX - manual_count)

        return {
            "date": data.get("date", cls._today_str()),
            "daily_limit": DAILY_AUTO_MAX,               # 50
            "auto_limit": DAILY_AUTO_MAX,                 # 50
            "manual_limit": DAILY_MANUAL_MAX,             # 20
            "total_limit": TOTAL_MAX_CEILING,             # 70
            "generated_today": auto_count,                # 50-quota bar tracks auto target
            "auto_published_today": auto_count,
            "manual_published_today": manual_count,
            "total_published_today": count,
            "remaining_today": remaining_auto,
            "remaining_auto": remaining_auto,
            "remaining_manual": remaining_manual,
            "auto_publish_stopped": auto_stopped,
            "auto_publish_stopped_reason": data.get("auto_publish_stopped_reason", ""),
            "percent_used": round((auto_count / DAILY_AUTO_MAX) * 100, 1),
            "allowed": (not auto_stopped) and (auto_count < DAILY_AUTO_MAX),
            "manual_allowed": (manual_count < DAILY_MANUAL_MAX) and (count < TOTAL_MAX_CEILING)
        }
