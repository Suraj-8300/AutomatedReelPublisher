import re
import random
from typing import Dict, Any, List
from .config import DURATION_TARGETS, PALETTES
from .idea_generator import VIRAL_NICHE_CATALOG, generate_random_topic

class PromptEnhancer:
    """
    Universal Reel Script & Storyboard Engine.
    Generates highly engaging, niche-adaptive scripts for ANY topic
    (psychology, wealth, history, tech, science, or custom user ideas)
    precisely timed for 10s, 15s, 30s, and 60s vertical Reels.
    """

    @staticmethod
    def enhance(user_prompt: str = None, duration: int = 15, theme: str = None) -> Dict[str, Any]:
        if duration not in [10, 15, 30, 60]:
            duration = 15

        # 1. Topic selection or dynamic generation
        if not user_prompt or user_prompt.strip() == "":
            topic_data = generate_random_topic()
        else:
            prompt = user_prompt.strip()
            # Check if it matches an existing catalog item
            matched = None
            for niche_items in VIRAL_NICHE_CATALOG.values():
                for item in niche_items:
                    if item["title"].lower() in prompt.lower() or prompt.lower() in item["title"].lower():
                        matched = item.copy()
                        break
                if matched:
                    break
            topic_data = matched if matched else PromptEnhancer._construct_dynamic_topic(prompt)

        # 2. Build narrative storyboard suited to duration and genre
        storyboard = PromptEnhancer._build_storyboard(topic_data, duration)

        # 3. Assign visual theme & duration
        if not theme or theme not in PALETTES:
            theme = topic_data.get("theme", "cyber_blue")
        storyboard["theme"] = theme
        storyboard["target_duration"] = duration
        storyboard["badge"] = topic_data.get("badge", "🔥 DID YOU KNOW?")

        return storyboard

    @staticmethod
    def _construct_dynamic_topic(prompt: str) -> Dict[str, Any]:
        """Dynamically parses and structures ANY custom prompt."""
        clean = prompt.rstrip("?").strip()
        lower = prompt.lower()

        # Stop words filter
        stop_words = {
            "the", "and", "for", "with", "from", "that", "this", "what", "when", 
            "where", "would", "could", "should", "about", "there", "their", 
            "plausible", "really", "actually", "make", "into", "some", "more", 
            "than", "over", "under", "been", "have", "were", "they", "them"
        }
        words = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', lower) if w not in stop_words]

        # Categorize genre and assign visual style
        if any(k in lower for k in ["money", "wealth", "rich", "billionaire", "invest", "crypto", "business", "tax"]):
            cat = "WEALTH & POWER"
            badge = "💰 WEALTH CODED"
            theme = "deep_emerald"
            keywords = words[:2] + ["money", "city", "skyscraper", "luxury"]
            takeaway = "The ultra-successful play by an entirely different set of financial rules."
        elif any(k in lower for k in ["brain", "psychology", "mind", "manipulation", "habit", "sleep", "attraction", "lie", "toxic"]):
            cat = "PSYCHOLOGY"
            badge = "🧠 MIND HACK"
            theme = "cyber_blue"
            keywords = words[:2] + ["thinking", "mind", "people", "talking"]
            takeaway = "Once you understand human psychology, you can never look at people the same way again."
        elif any(k in lower for k in ["ancient", "history", "rome", "egypt", "pyramid", "war", "emperor", "lost", "ruins"]):
            cat = "UNTOLD HISTORY"
            badge = "📜 UNTOLD HISTORY"
            theme = "crimson_flame"
            keywords = words[:2] + ["ancient", "architecture", "stone", "ruins"]
            takeaway = "History is rarely what was written in standard textbooks."
        elif any(k in lower for k in ["space", "galaxy", "black hole", "star", "planet", "alien", "universe", "nasa", "moon"]):
            cat = "COSMIC TRUTH"
            badge = "🌌 COSMIC TRUTH"
            theme = "cosmic_purple"
            keywords = words[:2] + ["space", "galaxy", "stars", "earth", "cosmos"]
            takeaway = "The sheer scale of the cosmos humbles everything we know."
        elif any(k in lower for k in ["ai", "robot", "quantum", "tech", "future", "algorithm", "code", "cyber"]):
            cat = "FUTURE TECH"
            badge = "⚡ FUTURE TECH"
            theme = "cyber_blue"
            keywords = words[:2] + ["digital", "technology", "circuit", "neon"]
            takeaway = "We are sprinting into a technological future faster than society can adapt."
        elif any(k in lower for k in ["workout", "fitness", "cold", "body", "health", "longevity", "fasting", "dopamine"]):
            cat = "BIOHACKING"
            badge = "🧬 BIOHACK"
            theme = "deep_emerald"
            keywords = words[:2] + ["fitness", "water", "cold", "medical", "health"]
            takeaway = "Small biological upgrades trigger massive neurological compounding."
        elif any(k in lower for k in ["plausible", "myth", "survive", "fall", "shark", "gun", "jump"]):
            cat = "MYTHBUSTER"
            badge = "🔬 IS IT PLAUSIBLE?"
            theme = "crimson_flame"
            keywords = words[:2] + ["science", "speed", "danger"]
            takeaway = "Intuition frequently fails when tested against physical laws."
        else:
            cat = "WILD CURIOSITY"
            badge = "🔥 DID YOU KNOW?"
            theme = "cyber_blue"
            keywords = words[:3] + ["nature", "city", "technology"]
            takeaway = "Reality is often stranger than the wildest fiction."

        # Generate engaging hook
        if lower.startswith("why ") or lower.startswith("how ") or lower.startswith("what "):
            hook = f"Did you know {clean.lower()}?"
        else:
            hook = f"Here is the mind-bending truth about {clean.lower()}."

        insight = f"When researchers and experts investigated the data, they discovered something completely counterintuitive."

        return {
            "category": cat,
            "badge": badge,
            "title": clean,
            "hook": hook,
            "insight": insight,
            "takeaway": takeaway,
            "theme": theme,
            "keywords": keywords
        }

    @staticmethod
    def _build_storyboard(topic: Dict[str, Any], duration: int) -> Dict[str, Any]:
        title = topic.get("title", "")
        hook = topic.get("hook", "")
        insight = topic.get("insight", "")
        takeaway = topic.get("takeaway", "")
        kw = topic.get("keywords", ["city", "technology", "nature"])

        # Helper to cascade keywords so primary is tested first, then other topic terms
        def scene_kw(primary_idx: int) -> List[str]:
            primary = kw[primary_idx] if primary_idx < len(kw) else (kw[0] if kw else "technology")
            rest = [k for k in kw if k != primary]
            return [primary] + rest

        # Pacing and script tuning per duration
        if duration == 10:
            # 10s: ~18-22 words. Instant punchy revelation.
            script = f"{hook} {insight.split('.')[0]}. {takeaway.split('.')[0]}!"
            scenes = [
                {"title": "THE HOOK", "text": hook, "keywords": scene_kw(0)},
                {"title": "THE REVEAL", "text": insight, "keywords": scene_kw(1)},
                {"title": "THE TAKEAWAY", "text": takeaway, "keywords": scene_kw(2)}
            ]

        elif duration == 15:
            # 15s: ~28-34 words. Viral Short structure.
            script = (
                f"{hook} Here is what actually happens. "
                f"{insight.split('.')[0]}. "
                f"The bottom line? {takeaway}"
            )
            scenes = [
                {"title": "THE HOOK", "text": hook, "keywords": scene_kw(0)},
                {"title": "THE INSIGHT", "text": insight, "keywords": scene_kw(1)},
                {"title": "THE TAKEAWAY", "text": takeaway, "keywords": scene_kw(2)}
            ]

        elif duration == 30:
            # 30s: ~65-72 words. Complete storytelling reel.
            script = (
                f"{hook} Most people go through life completely unaware of this. "
                f"When you look beneath the surface, the mechanism becomes crystal clear. "
                f"{insight} "
                f"Think about the implications of this. "
                f"{takeaway} "
                f"Follow for more daily mind-openers, and share this with someone who needs to hear it."
            )
            scenes = [
                {"title": "THE MYSTERY", "text": hook, "keywords": scene_kw(0)},
                {"title": "THE HIDDEN LAYER", "text": "What everyone overlooks.", "keywords": scene_kw(1)},
                {"title": "THE BREAKTHROUGH", "text": insight, "keywords": scene_kw(2)},
                {"title": "THE LESSON", "text": takeaway, "keywords": scene_kw(3)},
                {"title": "THE CALL TO ACTION", "text": "Follow for more daily revelations.", "keywords": scene_kw(0)}
            ]

        else: # 60 seconds
            # 60s: ~135-155 words. Deep documentary style.
            script = (
                f"Pay close attention, because what you are about to discover will change your entire perspective. "
                f"{hook} "
                f"On the surface, it seems totally counterintuitive. Society teaches us to expect one outcome, yet reality operates on completely different principles. "
                f"{insight} "
                f"Consider the profound ripple effects this creates across your everyday life. When you master this concept, the world starts making a lot more sense. "
                f"{takeaway} "
                f"Drop a comment with your thoughts below, hit follow for more powerful daily insights, and share this with someone who thinks differently."
            )
            scenes = [
                {"title": "THE AWAKENING", "text": hook, "keywords": scene_kw(0)},
                {"title": "THE COMMON TRAP", "text": "Why society gets this backwards.", "keywords": scene_kw(1)},
                {"title": "THE HIDDEN MECHANISM", "text": insight, "keywords": scene_kw(2)},
                {"title": "THE MASTER KEY", "text": takeaway, "keywords": scene_kw(3)},
                {"title": "THE TAKEAWAY", "text": "Follow for daily high-leverage insights.", "keywords": scene_kw(0)}
            ]

        return {
            "title": title,
            "badge": topic.get("badge", "🔥 DID YOU KNOW?"),
            "category": topic.get("category", "VIRAL INSIGHT"),
            "hook": hook,
            "script": script,
            "scenes": scenes,
            "keywords": kw
        }
