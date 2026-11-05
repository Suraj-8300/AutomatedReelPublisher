import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import CACHE_DIR

ANALYTICS_FILE = CACHE_DIR / "reel_analytics.json"

class LearningEngine:
    """
    Feedback-Driven Creative Optimization & Recommendation Engine.
    Tracks performance analytics (views, completion rate, shares, saves, likes)
    and dynamically adjusts future genre, hook, and caption weights.
    Supports A/B test variant generation.
    """

    @staticmethod
    def _load_data() -> Dict[str, Any]:
        if not ANALYTICS_FILE.exists():
            return {"reels": {}, "genre_scores": {}, "caption_scores": {}}
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"reels": {}, "genre_scores": {}, "caption_scores": {}}

    @staticmethod
    def _save_data(data: Dict[str, Any]):
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[LearningEngine Warning] Failed to save analytics: {e}")

    @staticmethod
    def record_metrics(
        video_filename: str,
        views: int = 0,
        completion_rate: float = 0.0,
        likes: int = 0,
        shares: int = 0,
        saves: int = 0,
        comments: int = 0
    ) -> Dict[str, Any]:
        """
        Records actual or estimated performance metrics for a reel.
        """
        data = LearningEngine._load_data()
        data["reels"][video_filename] = {
            "timestamp": time.time(),
            "views": views,
            "completion_rate": completion_rate,
            "likes": likes,
            "shares": shares,
            "saves": saves,
            "comments": comments
        }
        LearningEngine._save_data(data)
        return data["reels"][video_filename]

    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        data = LearningEngine._load_data()
        total_tracked = len(data["reels"])
        avg_completion = (
            sum(r.get("completion_rate", 0) for r in data["reels"].values()) / total_tracked
            if total_tracked > 0 else 0.0
        )
        return {
            "total_tracked_reels": total_tracked,
            "avg_completion_rate": round(avg_completion, 2)
        }

