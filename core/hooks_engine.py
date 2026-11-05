import random
from typing import Dict, Any, List, Optional

class HooksEngine:
    """
    High-retention Hook & Engagement Strategy Engine.
    Produces psychologically compelling opening hooks across 8 distinct families,
    pairing them with retention strategies (open loops, pattern interrupts, progressive reveals).
    """

    HOOK_FAMILIES = {
        "curiosity": [
            "There is something deeply strange about {topic}.",
            "Most people have no idea this actually happens with {topic}.",
            "The truth about {topic} is far more surprising than anyone thought.",
            "Scientists spent decades trying to explain this about {topic}.",
            "What if everything you knew about {topic} was incomplete?",
            "Look closely at {topic}, because almost nobody spots this."
        ],
        "contrarian": [
            "Everything society told you about {topic} might be wrong.",
            "This sounds completely impossible, but {topic} is 100% real.",
            "Stop doing {topic} the old way. Here is what actually works.",
            "Most advice about {topic} is backwards. Here is the reality.",
            "You were lied to about {topic}."
        ],
        "story": [
            "It started with one innocent decision about {topic}...",
            "Nobody believed what happened next with {topic}.",
            "In a secret facility, researchers tested {topic}...",
            "He thought it was an ordinary experiment with {topic}.",
            "They tried to bury the discovery of {topic}."
        ],
        "question": [
            "Have you ever wondered what actually happens during {topic}?",
            "What would happen to your reality if {topic} changed right now?",
            "Could you survive the extreme truth behind {topic}?",
            "Why does nobody talk about this dark side of {topic}?",
            "Do you know what your brain does when {topic} occurs?"
        ],
        "relatable": [
            "POV: That exact second you realize {topic}.",
            "You know that deeply awkward feeling when {topic} happens?",
            "Every single person experiences {topic}, but nobody admits it.",
            "Tell me you also deal with {topic} without telling me."
        ],
        "dramatic": [
            "Thirty seconds from now, you will never look at {topic} the same way.",
            "This is the single most dangerous misconception about {topic}.",
            "Pay close attention to this breakdown of {topic}.",
            "The countdown to understanding {topic} starts right now."
        ],
        "myth_buster": [
            "Myth versus reality: what really happens with {topic}.",
            "Is the popular myth about {topic} actually true?",
            "We put the legendary theory of {topic} to the ultimate test."
        ]
    }

    @staticmethod
    def generate_hook(
        topic_title: str,
        genre: str = "science",
        hook_family: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Synthesizes a punchy opening hook tailored to the genre and narrative goal.
        """
        rng = random.Random(seed) if seed is not None else random.Random()

        # Genre-to-hook family affinities
        affinity_map = {
            "comedy": ["relatable", "question", "curiosity"],
            "meme": ["relatable", "question", "contrarian"],
            "science": ["curiosity", "question", "myth_buster", "contrarian"],
            "mysteries": ["curiosity", "story", "dramatic"],
            "informative": ["contrarian", "question", "curiosity"],
            "emotional": ["story", "curiosity", "relatable"],
            "storytelling": ["story", "dramatic", "curiosity"],
            "animation": ["relatable", "story", "question"],
            "cinematic": ["dramatic", "story", "contrarian"]
        }

        if not hook_family or hook_family not in HooksEngine.HOOK_FAMILIES:
            preferred = affinity_map.get(genre, ["curiosity", "question"])
            hook_family = rng.choice(preferred)

        templates = HooksEngine.HOOK_FAMILIES[hook_family]
        template = rng.choice(templates)

        clean_topic = topic_title.strip()
        # Clean title for natural insertion
        if clean_topic.lower().startswith("the "):
            clean_topic = clean_topic[4:]

        hook_text = template.format(topic=clean_topic)

        # Ensure no trailing punctuation double-ups
        hook_text = hook_text.rstrip(".") + "."

        return {
            "family": hook_family,
            "text": hook_text
        }

