import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import CACHE_DIR

HISTORY_FILE = CACHE_DIR / "content_history.json"
MAX_HISTORY_ENTRIES = 200
DEFAULT_SIMILARITY_WINDOW = 30

class ContentHistory:
    """
    Persistent anti-repetition engine and content history tracker.
    Tracks previously generated topics, hooks, scripts, and creative combinations
    to enforce creative diversity and prevent repetition.
    """

    @staticmethod
    def _load_history() -> List[Dict[str, Any]]:
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _save_history(history: List[Dict[str, Any]]):
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history[-MAX_HISTORY_ENTRIES:], f, indent=2)
        except Exception as e:
            print(f"[ContentHistory Warning] Failed to save history: {e}")

    @staticmethod
    def record_generation(
        title: str,
        genre: str,
        subgenre: str,
        hook: str,
        script: str,
        seed: int,
        caption_style: str,
        music_style: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a newly generated Reel into the persistent content history.
        """
        history = ContentHistory._load_history()
        script_hash = hashlib.sha256(script.strip().encode("utf-8")).hexdigest()[:12]

        entry = {
            "id": f"reel_{int(time.time())}_{seed}",
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "title": title,
            "genre": genre,
            "subgenre": subgenre,
            "hook": hook,
            "script_hash": script_hash,
            "script_preview": script[:120],
            "seed": seed,
            "caption_style": caption_style,
            "music_style": music_style,
            "filename": filename or ""
        }

        history.append(entry)
        ContentHistory._save_history(history)
        return entry

    @staticmethod
    def is_concept_repetitive(
        title: str,
        hook: str,
        window_size: int = DEFAULT_SIMILARITY_WINDOW,
        threshold: float = 0.55
    ) -> bool:
        """
        Computes Jaccard word-similarity against recent history to check
        if this topic or hook was already produced recently.
        """
        history = ContentHistory._load_history()
        recent = history[-window_size:] if history else []

        if not recent:
            return False

        def tokenize(text: str) -> set:
            words = text.lower().replace("-", " ").replace("_", " ").split()
            # Filter trivial words
            stops = {"the", "a", "an", "is", "in", "of", "and", "to", "for", "with", "this", "that", "you", "your", "what", "why", "how"}
            return {w.strip(".,!?:;\"'") for w in words if w not in stops and len(w) > 2}

        cand_tokens = tokenize(f"{title} {hook}")
        if not cand_tokens:
            return False

        for past in recent:
            past_text = f"{past.get('title', '')} {past.get('hook', '')}"
            past_tokens = tokenize(past_text)
            if not past_tokens:
                continue

            intersection = cand_tokens.intersection(past_tokens)
            union = cand_tokens.union(past_tokens)
            similarity = len(intersection) / len(union) if union else 0.0

            if similarity >= threshold:
                return True

        return False

    @staticmethod
    def get_genre_distribution(window_size: int = 40) -> Dict[str, int]:
        """
        Returns the frequency of each genre generated in the recent window.
        """
        history = ContentHistory._load_history()
        recent = history[-window_size:] if history else []

        dist = {}
        for item in recent:
            g = item.get("genre", "other")
            dist[g] = dist.get(g, 0) + 1
        return dist

    @staticmethod
    def get_recent_history(limit: int = 15) -> List[Dict[str, Any]]:
        history = ContentHistory._load_history()
        return list(reversed(history[-limit:]))

