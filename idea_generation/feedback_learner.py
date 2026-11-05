"""
Feedback and Learning Engine for AutoReelStudio.
Absorbs performance insights from published Instagram Reels and YouTube Shorts
to continuously improve creative ideation, hook strength, and topic selection.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = DATA_DIR / "performance_history.json"

class FeedbackLearner:
    """Tracks published video metrics and computes creative weights."""

    @staticmethod
    def _load_history() -> List[Dict[str, Any]]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _save_history(records: List[Dict[str, Any]]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records[-200:], f, indent=2, ensure_ascii=False)

    @classmethod
    def record_publication(
        cls,
        video_id: str,
        title: str,
        genre: str,
        hook: str,
        platform: str,
        initial_score: float = 85.0
    ):
        """Records a published video entry for telemetry and learning."""
        records = cls._load_history()
        records.append({
            "video_id": video_id,
            "title": title,
            "genre": genre,
            "hook": hook,
            "platform": platform,
            "published_at": time.time(),
            "performance_score": initial_score,
            "views": 0,
            "likes": 0,
            "retention_rate": 0.0
        })
        cls._save_history(records)

    @classmethod
    def update_metrics(
        cls,
        video_id: str,
        views: int,
        likes: int,
        comments: int = 0,
        retention_rate: float = 0.0
    ):
        """Updates live metrics from Instagram or YouTube analytics."""
        records = cls._load_history()
        for r in records:
            if r.get("video_id") == video_id:
                r["views"] = views
                r["likes"] = likes
                r["comments"] = comments
                r["retention_rate"] = retention_rate
                # Compute composite performance score (0-100)
                engagement = (likes * 2 + comments * 5) / max(views, 1)
                r["performance_score"] = min(100.0, round(retention_rate * 50 + engagement * 1000 + 30, 1))
                break
        cls._save_history(records)

    @classmethod
    def get_genre_weights(cls) -> Dict[str, float]:
        """
        Computes dynamic multiplier weights per genre based on historical performance.
        Genres that perform better get higher probability of generation.
        """
        records = cls._load_history()
        if not records:
            return {}

        genre_scores: Dict[str, List[float]] = {}
        for r in records:
            g = r.get("genre", "science")
            genre_scores.setdefault(g, []).append(r.get("performance_score", 70.0))

        weights: Dict[str, float] = {}
        for g, scores in genre_scores.items():
            avg = sum(scores) / len(scores)
            weights[g] = round(avg / 70.0, 2)  # Normalized around 1.0
        return weights

