import random
import hashlib
from typing import Dict, Any, List, Optional

# Supported Genres and their Subgenres
GENRE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "comedy": {
        "label": "Funny & Comedy",
        "description": "Relatable humor, observational comedy, funny facts, situational skits",
        "subgenres": [
            "relatable_everyday",
            "situational_comedy",
            "unexpected_punchline",
            "observational_humor",
            "funny_facts",
            "awkward_situations",
            "dialogue_comedy"
        ],
        "default_voice": "en-US-ChristopherNeural",
        "speech_rate": "+8%",
        "music_styles": ["comedy_bounce", "curiosity_lofi", "cyber_pulse"],
        "caption_styles": ["meme", "high_impact", "karaoke"],
        "editing_styles": ["punchy_fast", "comic_timing"],
        "default_duration": 15,
        "badge": "😂 RELATABLE",
        "theme": "crimson_flame"
    },
    "meme": {
        "label": "Meme Reels",
        "description": "POV formats, trending meme tropes, reaction edits, tech/student life memes",
        "subgenres": [
            "pov_memes",
            "tech_and_code",
            "student_life",
            "workplace_humor",
            "expectation_vs_reality",
            "everyday_struggles"
        ],
        "default_voice": "en-US-ChristopherNeural",
        "speech_rate": "+10%",
        "music_styles": ["comedy_bounce", "cyber_pulse"],
        "caption_styles": ["meme", "high_impact"],
        "editing_styles": ["punchy_fast", "comic_timing"],
        "default_duration": 15,
        "badge": "💀 POV MEME",
        "theme": "cyber_blue"
    },
    "science": {
        "label": "Scientific & Educational",
        "description": "Space, physics, chemistry, biology, AI, robotics, verified discoveries",
        "subgenres": [
            "space_and_astronomy",
            "quantum_physics",
            "human_biology",
            "artificial_intelligence",
            "chemistry_wonders",
            "earth_and_climate",
            "engineering_marvels"
        ],
        "default_voice": "en-US-ChristopherNeural",
        "speech_rate": "+4%",
        "music_styles": ["cyber_pulse", "curiosity_lofi", "cinematic_drive"],
        "caption_styles": ["karaoke", "clean_minimal", "dynamic_phrase"],
        "editing_styles": ["documentary", "cinematic_smooth"],
        "default_duration": 30,
        "badge": "🔬 SCIENCE VERIFIED",
        "theme": "cyber_blue"
    },
    "mysteries": {
        "label": "Interesting Facts & Mysteries",
        "description": "Ancient history, cosmic anomalies, ocean depths, strange phenomena",
        "subgenres": [
            "ocean_abyss",
            "cosmic_anomalies",
            "ancient_mysteries",
            "unsolved_phenomena",
            "strange_nature",
            "historical_misconceptions"
        ],
        "default_voice": "en-US-GuyNeural",
        "speech_rate": "+0%",
        "music_styles": ["deep_mystery", "cinematic_drive", "horror_tension"],
        "caption_styles": ["cinematic", "dynamic_phrase", "karaoke"],
        "editing_styles": ["cinematic_smooth", "documentary"],
        "default_duration": 30,
        "badge": "🔍 UNTOLD MYSTERY",
        "theme": "cosmic_purple"
    },
    "informative": {
        "label": "Serious & Informative",
        "description": "Thought-provoking social observations, tech analysis, critical thinking",
        "subgenres": [
            "critical_thinking",
            "technology_analysis",
            "human_behavior",
            "social_dynamics",
            "practical_wisdom",
            "future_trends"
        ],
        "default_voice": "en-US-AndrewNeural",
        "speech_rate": "+2%",
        "music_styles": ["curiosity_lofi", "deep_mystery", "cyber_pulse"],
        "caption_styles": ["clean_minimal", "dynamic_phrase", "karaoke"],
        "editing_styles": ["documentary", "cinematic_smooth"],
        "default_duration": 30,
        "badge": "💡 DEEP INSIGHT",
        "theme": "deep_emerald"
    },
    "emotional": {
        "label": "Emotional & Motivational",
        "description": "Heartwarming moments, perseverance, friendship, inspirational short stories",
        "subgenres": [
            "perseverance_and_grit",
            "friendship_and_loyalty",
            "life_changing_moments",
            "silent_sacrifices",
            "heartwarming_realities",
            "meaningful_connections"
        ],
        "default_voice": "en-US-AvaNeural",
        "speech_rate": "-3%",
        "music_styles": ["emotional_piano", "curiosity_lofi"],
        "caption_styles": ["cinematic", "clean_minimal", "dynamic_phrase"],
        "editing_styles": ["cinematic_smooth"],
        "default_duration": 30,
        "badge": "✨ INSPIRATION",
        "theme": "deep_emerald"
    },
    "storytelling": {
        "label": "Storytelling & Narrative",
        "description": "Short fiction, suspense thrillers, sci-fi twists, multi-character narratives",
        "subgenres": [
            "psychological_thriller",
            "sci_fi_twist",
            "suspense_mystery",
            "two_character_dialogue",
            "unexpected_ending",
            "adventure_journey"
        ],
        "default_voice": "en-US-AvaNeural",
        "speech_rate": "+0%",
        "music_styles": ["cinematic_drive", "deep_mystery", "horror_tension"],
        "caption_styles": ["cinematic", "karaoke", "dynamic_phrase"],
        "editing_styles": ["cinematic_smooth", "comic_timing"],
        "default_duration": 30,
        "badge": "📖 THE STORY",
        "theme": "cosmic_purple"
    },
    "animation": {
        "label": "Animated Cartoons & Motion Comics",
        "description": "2D/3D cartoon skits, motion-comic storytelling, animated explainers",
        "subgenres": [
            "cartoon_comedy_skit",
            "motion_comic_story",
            "character_dialogue",
            "animated_explainer",
            "funny_character_interaction"
        ],
        "default_voice": "en-US-ChristopherNeural",
        "speech_rate": "+6%",
        "music_styles": ["comedy_bounce", "cyber_pulse", "curiosity_lofi"],
        "caption_styles": ["meme", "high_impact", "karaoke"],
        "editing_styles": ["comic_timing", "punchy_fast"],
        "default_duration": 15,
        "badge": "🎨 ANIMATED SKIT",
        "theme": "cyber_blue"
    },
    "cinematic": {
        "label": "Movie Edits & Action Scenes",
        "description": "Dramatic speeches, trailer-style tension, heroic journeys, cinematic edits",
        "subgenres": [
            "dramatic_monologue",
            "trailer_tension",
            "heroic_journey",
            "action_sequence",
            "cinematic_philosophy"
        ],
        "default_voice": "en-US-GuyNeural",
        "speech_rate": "-2%",
        "music_styles": ["action_hybrid", "cinematic_drive", "deep_mystery"],
        "caption_styles": ["cinematic", "high_impact", "clean_minimal"],
        "editing_styles": ["cinematic_smooth", "punchy_fast"],
        "default_duration": 30,
        "badge": "🎬 CINEMATIC",
        "theme": "crimson_flame"
    },
    "animal_story": {
        "label": "🐾 AI Animal Storyteller",
        "description": "Engaging mini-movies of animals doing human-like activities across 6 visual styles",
        "subgenres": [
            "pixar_3d_adventure",
            "photorealistic_nature",
            "ghibli_2d_cartoon",
            "anime_wonder",
            "stop_motion_clay",
            "fantasy_creatures"
        ],
        "default_voice": "en-US-JennyNeural",
        "speech_rate": "-2%",
        "music_styles": ["cozy_acoustic", "playful_bounce", "magical_fantasy", "cinematic_adventure"],
        "caption_styles": ["cinematic", "clean_minimal", "karaoke"],
        "editing_styles": ["cinematic_smooth"],
        "default_duration": 15,
        "badge": "🐾 ANIMAL STORY",
        "theme": "cozy_warm"
    }
}

# Generation Modes with Genre Distribution Weights
GENERATION_MODES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "comedy": 0.15,
        "meme": 0.12,
        "science": 0.18,
        "mysteries": 0.15,
        "informative": 0.10,
        "emotional": 0.10,
        "storytelling": 0.10,
        "animation": 0.05,
        "cinematic": 0.05
    },
    "comedy": {
        "comedy": 0.50,
        "meme": 0.35,
        "animation": 0.15
    },
    "educational": {
        "science": 0.50,
        "mysteries": 0.30,
        "informative": 0.20
    },
    "story": {
        "storytelling": 0.45,
        "emotional": 0.30,
        "animation": 0.15,
        "mysteries": 0.10
    },
    "cinematic": {
        "cinematic": 0.50,
        "storytelling": 0.25,
        "mysteries": 0.25
    },
    "animal_story": {
        "animal_story": 1.0
    },
    "surprise": {
        "comedy": 0.11,
        "meme": 0.11,
        "science": 0.11,
        "mysteries": 0.11,
        "informative": 0.11,
        "emotional": 0.11,
        "storytelling": 0.11,
        "animation": 0.12,
        "cinematic": 0.12
    }
}

class CreativeRandomizer:
    """
    Intelligent Structured Creative Randomization Engine.
    Samples compatible, genre-aware creative parameters across 14 dimensions:
    genre, subgenre, topic, format, hook, narrative, visual approach,
    editing style, caption style, voice, speech rate, music style, duration, ending.
    """

    @staticmethod
    def generate_creative_config(
        mode: str = "balanced",
        genre_preference: Optional[str] = None,
        duration_preference: Optional[int] = None,
        caption_style_preference: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Samples an integrated, coherent creative configuration.
        """
        rng = random.Random(seed) if seed is not None else random.Random()
        actual_seed = seed if seed is not None else rng.randint(100000, 999999)

        # 1. Resolve Mode & Genre
        clean_mode = mode.lower() if mode and mode.lower() in GENERATION_MODES else "balanced"
        mode_weights = GENERATION_MODES[clean_mode]

        if genre_preference and genre_preference.lower() in GENRE_TAXONOMY:
            selected_genre = genre_preference.lower()
        else:
            genres = list(mode_weights.keys())
            weights = list(mode_weights.values())
            selected_genre = rng.choices(genres, weights=weights, k=1)[0]

        genre_meta = GENRE_TAXONOMY[selected_genre]

        # 2. Select Subgenre
        subgenres = genre_meta["subgenres"]
        selected_subgenre = rng.choice(subgenres)

        # 3. Determine Duration
        if duration_preference in [10, 15, 30, 60]:
            selected_duration = duration_preference
        else:
            # Short format for comedy/meme/animation, medium for stories/science
            if selected_genre in ["comedy", "meme", "animation"]:
                selected_duration = rng.choice([10, 15, 30])
            elif selected_genre in ["storytelling", "cinematic", "emotional"]:
                selected_duration = rng.choice([30, 60])
            else:
                selected_duration = rng.choice([15, 30, 60])

        # 4. Resolve Caption Style
        if caption_style_preference and caption_style_preference in [
            "karaoke", "high_impact", "clean_minimal", "cinematic", "dynamic_phrase", "meme"
        ]:
            selected_caption_style = caption_style_preference
        else:
            selected_caption_style = rng.choice(genre_meta["caption_styles"])

        # 5. Resolve Voice & Speed
        selected_voice = genre_meta["default_voice"]
        selected_speech_rate = genre_meta["speech_rate"]
        # Allow slight variation in voice for variety
        if rng.random() > 0.4 and selected_genre in ["storytelling", "emotional"]:
            selected_voice = rng.choice(["en-US-AvaNeural", "en-US-JennyNeural", "en-US-AndrewNeural"])
        elif rng.random() > 0.5 and selected_genre in ["science", "mysteries"]:
            selected_voice = rng.choice(["en-US-ChristopherNeural", "en-US-GuyNeural", "en-US-AndrewNeural"])

        # 6. Resolve Music Track
        selected_music = rng.choice(genre_meta["music_styles"])

        # 7. Resolve Editing Style
        selected_editing = rng.choice(genre_meta["editing_styles"])

        # 8. Visual Approach
        if selected_genre == "animation":
            visual_approach = "cartoon_animation"
        elif selected_genre == "cinematic":
            visual_approach = rng.choice(["cinematic_grade", "dynamic_pan_zoom", "stock_footage"])
        elif selected_genre in ["comedy", "meme"]:
            visual_approach = rng.choice(["stock_footage", "dynamic_pan_zoom", "procedural_art"])
        else:
            visual_approach = rng.choice(["stock_footage", "dynamic_pan_zoom", "motion_graphics"])

        # 9. Format & Narrative Pattern
        format_options = {
            "comedy": ["situational_skit", "observational_monologue", "punchline_reveal"],
            "meme": ["pov_format", "relatable_breakdown", "expectation_vs_reality"],
            "science": ["curiosity_explainer", "breakthrough_breakdown", "myth_vs_reality"],
            "mysteries": ["intrigue_investigation", "clue_progression", "unsolved_timeline"],
            "informative": ["thought_experiment", "deep_dive", "counterintuitive_truth"],
            "emotional": ["short_story", "inspirational_moment", "life_lesson"],
            "storytelling": ["narrative_twist", "two_character_conflict", "suspense_reveal"],
            "animation": ["character_skit", "motion_comic", "visual_parable"],
            "cinematic": ["dramatic_montage", "trailer_cut", "heroic_monologue"]
        }
        selected_format = rng.choice(format_options.get(selected_genre, ["curiosity_explainer"]))

        # 10. Ending Strategy
        ending_options = {
            "comedy": ["unexpected_twist", "deadpan_punchline", "relatable_callback"],
            "meme": ["abrupt_punchline", "relatable_question", "loop_payoff"],
            "science": ["fascinating_takeaway", "open_question", "cosmic_perspective"],
            "mysteries": ["lingering_intrigue", "compelling_theory", "curiosity_gap"],
            "informative": ["actionable_insight", "mindset_shift", "discussion_prompt"],
            "emotional": ["heartfelt_truth", "inspiring_call", "lasting_thought"],
            "storytelling": ["surprise_twist", "satisfying_closure", "open_loop"],
            "animation": ["humorous_payoff", "visual_callback", "playful_ending"],
            "cinematic": ["impactful_statement", "fade_to_black", "climactic_resolve"]
        }
        selected_ending = rng.choice(ending_options.get(selected_genre, ["fascinating_takeaway"]))

        return {
            "seed": actual_seed,
            "mode": clean_mode,
            "genre": selected_genre,
            "genre_label": genre_meta["label"],
            "subgenre": selected_subgenre,
            "badge": genre_meta["badge"],
            "theme": genre_meta["theme"],
            "duration": selected_duration,
            "format": selected_format,
            "caption_style": selected_caption_style,
            "voice": selected_voice,
            "speech_rate": selected_speech_rate,
            "music_style": selected_music,
            "editing_style": selected_editing,
            "visual_approach": visual_approach,
            "ending_strategy": selected_ending
        }

