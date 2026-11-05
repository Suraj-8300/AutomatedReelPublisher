"""
Idea Queue Manager for AutoReelStudio.
Maintains a persistent buffer queue of 10 to 15 high-quality pre-approved ideas.
Enforces the replenishment rule:
  - If queue < 10 ideas: automatically generates more until buffer reaches 15.
  - If queue >= 10 ideas: halts generation to conserve compute until consumed.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .research_engine import IdeaResearchEngine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUEUE_FILE = DATA_DIR / "idea_queue.json"

MIN_QUEUE_THRESHOLD = 10
TARGET_QUEUE_SIZE = 15

class IdeaQueueManager:
    """Manages the persistent 10-15 creative idea buffer queue."""

    @staticmethod
    def _load_queue() -> List[Dict[str, Any]]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not QUEUE_FILE.exists():
            return []
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _save_queue(queue: List[Dict[str, Any]]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_queue(cls) -> List[Dict[str, Any]]:
        """Returns the current list of queued ideas."""
        return cls._load_queue()

    @classmethod
    def get_count(cls) -> int:
        """Returns the number of ideas currently in the queue."""
        return len(cls._load_queue())

    @classmethod
    def replenish_if_needed(cls, target_size: int = TARGET_QUEUE_SIZE) -> Dict[str, Any]:
        """
        Enforces the replenishment policy:
        If queue count is < 10, generates new ideas until it reaches target_size (15).
        If queue count is >= 10, stops generation.
        """
        queue = cls._load_queue()
        initial_count = len(queue)

        if initial_count >= MIN_QUEUE_THRESHOLD:
            return {
                "action": "paused",
                "message": f"Idea buffer sufficient ({initial_count} ideas). Generation paused.",
                "initial_count": initial_count,
                "current_count": initial_count,
                "generated": 0
            }

        needed = max(0, target_size - initial_count)
        print(f"💡 [IdeaQueue] Buffer below threshold ({initial_count} < {MIN_QUEUE_THRESHOLD}). Replenishing {needed} ideas...")

        existing_titles = {item.get("title") for item in queue}
        generated = 0
        attempts = 0

        while len(queue) < target_size and attempts < needed * 3:
            attempts += 1
            idea = IdeaResearchEngine.generate_creative_idea()
            if idea["title"] not in existing_titles:
                queue.append(idea)
                existing_titles.add(idea["title"])
                generated += 1

        cls._save_queue(queue)
        print(f"✅ [IdeaQueue] Replenished {generated} ideas. Current buffer: {len(queue)} ideas.")

        return {
            "action": "replenished",
            "message": f"Generated {generated} ideas to reach target buffer ({len(queue)} total).",
            "initial_count": initial_count,
            "current_count": len(queue),
            "generated": generated
        }

    @classmethod
    def pop_next_idea(cls, auto_replenish: bool = True) -> Optional[Dict[str, Any]]:
        """
        Pops the next available idea from the front of the queue.
        Triggers replenishment if the queue drops below MIN_QUEUE_THRESHOLD.
        """
        queue = cls._load_queue()
        if not queue:
            # Emergency fallback: generate one immediately
            idea = IdeaResearchEngine.generate_creative_idea()
            if auto_replenish:
                cls.replenish_if_needed()
            return idea

        selected = queue.pop(0)
        cls._save_queue(queue)

        # Check if replenishment is needed after consumption
        if auto_replenish and len(queue) < MIN_QUEUE_THRESHOLD:
            cls.replenish_if_needed()

        return selected

    @classmethod
    def peek_next_idea(cls) -> Optional[Dict[str, Any]]:
        """Returns the next idea in queue without removing it."""
        queue = cls._load_queue()
        return queue[0] if queue else None

    @classmethod
    def add_idea(cls, idea: Dict[str, Any]) -> bool:
        """Adds an idea to the queue up to maximum buffer size."""
        queue = cls._load_queue()
        if len(queue) >= TARGET_QUEUE_SIZE:
            return False
        queue.append(idea)
        cls._save_queue(queue)
        return True

    @classmethod
    def remove_idea(cls, idea_id: str) -> bool:
        """Removes a specific idea by ID."""
        queue = cls._load_queue()
        new_queue = [item for item in queue if item.get("id") != idea_id]
        if len(new_queue) != len(queue):
            cls._save_queue(new_queue)
            return True
        return False
