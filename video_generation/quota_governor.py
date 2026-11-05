"""
Daily Quota Governor for AutoReelStudio.
Enforces the 50 reels/day ceiling to prevent platform throttling and rate limits.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUOTA_FILE = DATA_DIR / "daily_quota.json"

DAILY_MAX_REELS = 50

class QuotaGovernor:
    """Tracks and enforces the 50 reels per day safety ceiling."""

    @staticmethod
    def _today_str() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @classmethod
    def _load_data(cls) -> Dict[str, Any]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not QUOTA_FILE.exists():
            return {"date": cls._today_str(), "count": 0, "history": {}}
        try:
            with open(QUOTA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") != cls._today_str():
                    # Archive yesterday's count
                    old_date = data.get("date")
                    old_count = data.get("count", 0)
                    history = data.get("history", {})
                    if old_date:
                        history[old_date] = old_count
                    data = {"date": cls._today_str(), "count": 0, "history": history}
                    cls._save_data(data)
                return data
        except Exception:
            return {"date": cls._today_str(), "count": 0, "history": {}}

    @classmethod
    def _save_data(cls, data: Dict[str, Any]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUOTA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def can_generate(cls) -> Tuple[bool, int, str]:
        """
        Checks if a new Reel can be generated today.
        Returns: (allowed: bool, remaining_today: int, message: str)
        """
        data = cls._load_data()
        count = data.get("count", 0)
        remaining = max(0, DAILY_MAX_REELS - count)

        if count >= DAILY_MAX_REELS:
            msg = f"⛔ Daily quota reached: {count}/{DAILY_MAX_REELS} Reels generated today. Resets at 00:00 UTC."
            return False, 0, msg

        msg = f"✅ Quota OK: {count}/{DAILY_MAX_REELS} generated today ({remaining} remaining)."
        return True, remaining, msg

    @classmethod
    def record_generation(cls) -> int:
        """Increments today's generated count and returns the updated count."""
        data = cls._load_data()
        data["count"] = data.get("count", 0) + 1
        cls._save_data(data)
        return data["count"]

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns comprehensive quota telemetry."""
        data = cls._load_data()
        count = data.get("count", 0)
        remaining = max(0, DAILY_MAX_REELS - count)
        return {
            "date": data.get("date", cls._today_str()),
            "daily_limit": DAILY_MAX_REELS,
            "generated_today": count,
            "remaining_today": remaining,
            "percent_used": round((count / DAILY_MAX_REELS) * 100, 1),
            "allowed": count < DAILY_MAX_REELS
        }
