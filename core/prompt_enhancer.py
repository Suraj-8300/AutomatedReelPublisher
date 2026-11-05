import re
import random
from typing import Dict, Any, List, Optional
from .config import DURATION_TARGETS, PALETTES
from .creative_randomizer import CreativeRandomizer, GENRE_TAXONOMY
from .content_history import ContentHistory
from .hooks_engine import HooksEngine
from .idea_generator import IdeaGenerator
from .broll_engine import SYNONYM_MAP
from .animal_storyteller import AnimalStoryteller

class PromptEnhancer:
    """
    Intelligent Storyboard & Dynamic Script Generation Engine.
    Supports:
    1. Infinite autonomous generative idea creation (never fixed, never static).
    2. Dynamic custom prompt enhancement: user inputs any topic/idea and the engine
       builds a complete, tailored vertical Reel around it.
    """

    @staticmethod
    def enhance(
        user_prompt: Optional[str] = None,
        duration: int = 15,
        theme: Optional[str] = None,
        genre: Optional[str] = None,
        subgenre: Optional[str] = None,
        mode: str = "balanced",
        caption_style: Optional[str] = None,
        seed: Optional[int] = None,
        animal_species: Optional[str] = None,
        visual_style: Optional[str] = None,
        activity_type: Optional[str] = None,
        is_duo: bool = False
    ) -> Dict[str, Any]:
        """
        Generates a rich, genre-aware storyboard.
        Supports standard multi-genre Reels as well as AI Animal & Character Storytelling.
        """
        if duration not in [10, 15, 30, 60]:
            duration = 15

        # Check for AI Animal & Character Storytelling Mode
        is_animal_request = (
            mode == "animal_story" or
            genre == "animal_story" or
            bool(animal_species) or
            bool(visual_style) or
            is_duo or
            (user_prompt and any(w in user_prompt.lower() for w in [
                "kitten", "puppy", "capybara", "panda", "bunny", "duckling", "otter", "raccoon"
            ]) and mode in ["story", "balanced", "animal_story"])
        )

        if is_animal_request:
            storyboard = AnimalStoryteller.generate_story(
                animal_species=animal_species,
                is_duo=is_duo,
                visual_style=visual_style,
                story_genre=genre if genre in ["cute", "funny", "adventure", "emotional", "unexpected_funny", "educational"] else None,
                activity_type=activity_type,
                duration=duration,
                custom_concept=user_prompt,
                seed=seed
            )
            if caption_style:
                storyboard["caption_style"] = caption_style
            if theme and theme in PALETTES:
                storyboard["theme"] = theme
            return storyboard

        # 1. Sample Creative Configuration
        config = CreativeRandomizer.generate_creative_config(
            mode=mode,
            genre_preference=genre,
            duration_preference=duration,
            caption_style_preference=caption_style,
            seed=seed
        )

        selected_genre = config["genre"]
        selected_subgenre = config["subgenre"]
        selected_seed = config["seed"]

        # 2. Topic Resolution: User Custom Idea vs Infinite Autonomous Generation
        if user_prompt and user_prompt.strip():
            # User provided their own idea -> build completely around it
            topic_data = IdeaGenerator.enhance_custom_prompt(
                prompt=user_prompt.strip(),
                genre_preference=genre or selected_genre,
                duration=duration
            )
            selected_genre = topic_data["genre"]
        else:
            # Autonomous generation: generate fresh idea on the fly
            topic_data = IdeaGenerator.generate_autonomous_idea(
                genre=selected_genre,
                subgenre=selected_subgenre,
                duration=duration,
                seed=selected_seed
            )

            # Anti-repetition check: if similar concept was recently generated, re-roll with a new seed
            attempts = 0
            while ContentHistory.is_concept_repetitive(topic_data["title"], topic_data["hook"]) and attempts < 5:
                selected_seed += 101
                topic_data = IdeaGenerator.generate_autonomous_idea(
                    genre=selected_genre,
                    subgenre=selected_subgenre,
                    duration=duration,
                    seed=selected_seed
                )
                attempts += 1

        # 3. Clean script from any AI clichés and split into visual scenes
        clean_script = PromptEnhancer._clean_script_cliches(topic_data["script"])
        scenes = PromptEnhancer._plan_scenes(clean_script, topic_data["keywords"], duration, selected_genre)

        # 4. Integrate Creative Metadata
        resolved_theme = theme if (theme and theme in PALETTES) else topic_data.get("theme", config["theme"])

        return {
            "title": topic_data["title"],
            "hook": topic_data.get("hook", ""),
            "script": clean_script,
            "scenes": scenes,
            "keywords": topic_data.get("keywords", ["technology", "city"]),
            "theme": resolved_theme,
            "target_duration": duration,
            "badge": topic_data.get("badge", config["badge"]),
            "genre": selected_genre,
            "subgenre": topic_data.get("subgenre", selected_subgenre),
            "caption_style": config["caption_style"],
            "voice": config["voice"],
            "speech_rate": config["speech_rate"],
            "music_style": config["music_style"],
            "editing_style": config["editing_style"],
            "visual_approach": config["visual_approach"],
            "seed": selected_seed,
            "source": topic_data.get("source", "Autonomous Synthesis")
        }

    @staticmethod
    def _clean_script_cliches(script: str) -> str:
        """Removes robotic AI clichés and filler phrases."""
        cliches = [
            r"pay close attention,?\s*",
            r"hello guys,?\s*",
            r"welcome back,?\s*",
            r"in this video,?\s*",
            r"drop a comment below,?\s*",
            r"hit the subscribe button,?\s*",
            r"smash the like button,?\s*",
            r"make sure to follow,?\s*",
            r"did you know that\s+"
        ]
        cleaned = script
        for c in cliches:
            cleaned = re.sub(c, "", cleaned, flags=re.IGNORECASE)

        cleaned = ". ".join(s.strip().capitalize() for s in cleaned.split(".") if s.strip())
        if cleaned and not cleaned.endswith((".", "!", "?")):
            cleaned += "."
        return cleaned

    @staticmethod
    def _plan_scenes(script: str, keywords: List[str], duration: int, genre: str) -> List[Dict[str, Any]]:
        """Splits the script into visual scenes with keyword progression."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', script) if s.strip()]
        if not sentences:
            sentences = [script]

        if duration <= 15:
            num_scenes = min(3, max(2, len(sentences)))
        elif duration <= 30:
            num_scenes = min(4, max(3, len(sentences)))
        else:
            num_scenes = min(6, max(4, len(sentences)))

        scenes = []
        words = script.split()
        chunk_size = max(1, len(words) // num_scenes)

        for i in range(num_scenes):
            scene_text = sentences[i] if i < len(sentences) else " ".join(words[i * chunk_size:(i + 1) * chunk_size])

            # Find keywords mentioned directly in this specific scene's text
            scene_words = re.findall(r'\b[a-zA-Z]{3,}\b', scene_text.lower())
            direct_matches = [w for w in scene_words if w in SYNONYM_MAP]

            if direct_matches:
                kw_primary = direct_matches[0]
                kw_secondary = direct_matches[1] if len(direct_matches) > 1 else (keywords[i % len(keywords)] if keywords else kw_primary)
            else:
                kw_primary = keywords[i % len(keywords)] if keywords else "technology"
                kw_secondary = keywords[(i + 1) % len(keywords)] if len(keywords) > 1 else kw_primary

            scenes.append({
                "index": i,
                "title": f"SCENE_{i+1}",
                "text": scene_text,
                "keywords": [kw_primary, kw_secondary]
            })

        return scenes
