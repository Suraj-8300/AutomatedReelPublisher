"""
Pillar Router — determines which video generation engine to use for a topic.
"""
from video.sources.topic_rotator import TopicRotator


class PillarRouter:
    """Routes a topic to the correct content pillar."""

    VALID_PILLARS = {"cinematic", "science", "mechanical", "explainer", "animal_story", "storytelling", "cute_animals"}

    @classmethod
    def route(cls, topic: str, pillar_override: str = None) -> str:
        """
        Returns the content pillar for a topic.
        Uses override if provided and valid, otherwise auto-detects.
        """
        if pillar_override and pillar_override in cls.VALID_PILLARS:
            if pillar_override in ("storytelling", "cute_animals"):
                return "animal_story"
            return pillar_override
        detected = TopicRotator.detect_pillar(topic)
        if detected in ("storytelling", "cute_animals"):
            return "animal_story"
        return detected
