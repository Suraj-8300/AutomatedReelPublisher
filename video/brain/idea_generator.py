"""
Two-Stage Gemini Viral Idea & Reel Concept Generator for AutoReelStudio.

Stage 1: Prompts Gemini for a high-retention viral concept prompt and core subject entity.
Stage 2: Feeds that viral prompt back to Gemini to generate the synchronized 3-Act script,
         narration, and strictly entity-bound video search queries (zero random clips).
"""

import json
import random
from typing import Dict, Any, Optional

from video.brain.script_writer import _call_gemini, _extract_json
from video.brain.character_director import CharacterDirector


class IdeaGenerator:
    """
    Automated 2-Stage Reels Idea Generator using Gemini 2.5 Flash.
    Eliminates manual topic brainstorming and ensures high retention and visual-audio sync.
    """

    @classmethod
    def generate_viral_prompt(cls, pillar: str = "animal_story") -> Dict[str, Any]:
        """
        Stage 1: Ask Gemini for a high-engaging, psychology-backed reels concept prompt.
        Focuses on scroll-stopping hooks, high-retention narrative arcs, and emotional resonance.
        """
        if pillar in ("animal_story", "storytelling", "cute_animals"):
            focus = (
                "Create a high-retention cute animal storytelling or emotional rescue concept "
                "(like The Dodo, GeoBeats, or Little Things). "
                "The concept must focus on a SINGLE core subject entity (e.g. golden retriever puppy, "
                "orange tabby kitten, baby duckling, orphaned otter, baby owl) with a powerful 3-part emotional journey: "
                "1) Vulnerable / lonely struggle, 2) Gentle human kindness and trust building, 3) Joyful thriving transformation."
            )
        elif pillar == "science":
            focus = (
                "Create a mind-blowing, breakthrough science documentary concept (space, genetics, quantum, ocean). "
                "Identify a single core subject entity (e.g., James Webb telescope, deep-sea glowing creature, CRISPR, Mars rover) "
                "with an irresistible curiosity hook and jaw-dropping revelation."
            )
        elif pillar == "mechanical":
            focus = (
                "Create a high-retention mechanical or engineering explainer concept. "
                "Identify a single machine or mechanism (e.g., jet engine, differential gear, turbocharger, submarine ballast) "
                "focused on how the physical components move and deliver kinetic force."
            )
        else:
            focus = (
                "Create an awe-inspiring vertical video storytelling concept. "
                "Identify a single core subject with an irresistible hook, surprising escalation, and memorable punchline."
            )

        prompt = f"""You are an elite short-form video retention strategist for Instagram Reels and YouTube Shorts.
Your goal is to formulate a high-engaging, psychology-backed video concept prompt that guarantees maximum watch time, comments, and shares.

{focus}

Return ONLY valid JSON in this exact structure:
{{
  "topic": "Catchy, curiosity-inducing title (4-6 words)",
  "subject_entity": "The single primary subject (e.g. 'golden retriever puppy', 'orange kitten', 'baby duckling', 'jet engine')",
  "viral_prompt": "Detailed narrative concept describing the exact hook, the emotional/mechanic escalation, and the payoff (60-100 words)",
  "target_emotion": "one of: heartwarming, awe, curiosity, inspiration, satisfaction",
  "voice_style": "female or documentary",
  "music_style": "heartwarming_story, ambient_glow, or cyber_pulse"
}}
"""
        raw = _call_gemini(prompt, temperature=0.85)
        data = _extract_json(raw)

        if not data or not data.get("topic") or not data.get("subject_entity"):
            # Resilient fallback
            data = {
                "topic": "A Tiny Kitten's Big Comeback",
                "subject_entity": "kitten",
                "viral_prompt": "A tiny shivering kitten huddled alone outside in the cold is rescued by gentle hands, wrapped in warmth, and blossoms into a playful, joyful companion full of life.",
                "target_emotion": "heartwarming",
                "voice_style": "female",
                "music_style": "heartwarming_story"
            }

        return data

    @classmethod
    def generate_synchronized_reel_idea(cls, pillar: str = "animal_story") -> Dict[str, Any]:
        """
        Full 2-Stage Pipeline:
        1. Formulate high-engaging viral prompt from Gemini.
        2. Feed prompt back to Gemini to generate the synchronized 3-Act script
           with character continuity, locked visual tokens, and entity-bound queries.
        """
        print("🧠 Stage 1: Brainstorming high-engagement viral concept from Gemini...")
        prompt_data = cls.generate_viral_prompt(pillar=pillar)
        topic = prompt_data.get("topic", "An Extraordinary Story")
        subject = prompt_data.get("subject_entity", "cute animal")
        viral_prompt = prompt_data.get("viral_prompt", "")
        voice_style = prompt_data.get("voice_style", "female")
        music_style = prompt_data.get("music_style", "heartwarming_story")

        # Create persistent character continuity profile
        char_profile = None
        character_token = ""
        seed = random.randint(1000, 99999)

        if pillar in ("animal_story", "storytelling", "cute_animals", "anthropomorphic_animal"):
            char_profile = CharacterDirector.create_character_profile(
                species=subject.split()[-1] if subject else "kitten",
                seed=seed
            )
            character_token = char_profile.get("character_token", "")
            print(f"   🐾 Character Profile: {char_profile['label']} named '{char_profile['name']}'")
            print(f"   🔒 Consistency Token: {character_token[:80]}...")

        print(f"   💡 Concept: '{topic}'")
        print(f"   🎯 Subject Entity: '{subject}'")

        print("✍️  Stage 2: Generating entity-synchronized 3-Act script with character continuity...")
        stage2_prompt = f"""You are a master viral vertical video scriptwriter.
Using this viral concept and subject:
Topic: {topic}
Subject Entity: {subject}
Concept: {viral_prompt}
Pillar: {pillar}
Character Visual Token: {character_token}

Write a high-retention 25-30 second vertical script formatted for Instagram Reels and YouTube Shorts.

CRITICAL REQUIREMENTS FOR PERFECT VISUAL-AUDIO SYNCHRONIZATION AND CHARACTER CONTINUITY:
1. Every scene's spoken sentence ('text') must describe what is happening in the visual.
2. For every scene, 'prompt' MUST depict the EXACT SAME CHARACTER and SETTING.
   - Start the prompt with: '{character_token}' (if provided) or '{subject}'.
   - Then describe the specific action and camera angle for that scene.
   - Add: 'photorealistic, 8k, cinematic lighting, 9:16 vertical'.
3. 'search_queries' MUST specifically pair '{subject}' with the scene's exact action.

Return ONLY valid JSON in this exact structure:
{{
  "title": "{topic}",
  "subject_entity": "{subject}",
  "character_token": "{character_token}",
  "hook": "Opening hook sentence (max 15 words)",
  "escalation": "2 sentences explaining the turning point or care",
  "payoff": "1 sentence delivering the joyful or inspiring payoff",
  "voice_style": "{voice_style}",
  "music_style": "{music_style}",
  "scenes": [
    {{
      "scene_num": 1,
      "text": "Exact spoken narration for scene 1 (15-20 words)",
      "prompt": "{character_token}, scene 1 action showing {subject}, wide establishing shot, cinematic lighting, 8k, 9:16 vertical",
      "visual_action": "Specific visual action showing {subject}",
      "search_queries": ["query 1 with {subject}", "query 2 with {subject}"]
    }},
    {{
      "scene_num": 2,
      "text": "Exact spoken narration for scene 2 (20-25 words)",
      "prompt": "{character_token}, scene 2 action showing {subject}, medium action shot, warm lighting, 8k, 9:16 vertical",
      "visual_action": "Specific visual action showing {subject}",
      "search_queries": ["query 1 with {subject}", "query 2 with {subject}"]
    }},
    {{
      "scene_num": 3,
      "text": "Exact spoken narration for scene 3 (15-20 words)",
      "prompt": "{character_token}, scene 3 action showing {subject}, joyful close-up payoff shot, golden lighting, 8k, 9:16 vertical",
      "visual_action": "Specific visual action showing {subject}",
      "search_queries": ["query 1 with {subject}", "query 2 with {subject}"]
    }}
  ]
}}
"""
        raw2 = _call_gemini(stage2_prompt, temperature=0.7)
        script_data = _extract_json(raw2)

        # Build full narration from scene texts
        scenes = script_data.get("scenes", [])
        if scenes:
            scene_texts = [s.get("text", "").strip() for s in scenes if s.get("text")]
            if scene_texts:
                script_data["narration"] = " ".join(scene_texts)

        if not script_data.get("narration"):
            hook = script_data.get("hook", "").strip()
            escalation = script_data.get("escalation", "").strip()
            payoff = script_data.get("payoff", "").strip()
            script_data["narration"] = f"{hook} {escalation} {payoff}".strip()

        # Inject subject entity, character token, and seed into script_data
        script_data["topic"] = topic
        script_data["subject_entity"] = subject
        script_data["pillar"] = pillar
        script_data["character_token"] = character_token or script_data.get("character_token", "")
        script_data["seed"] = seed
        if char_profile:
            script_data["character_profile"] = char_profile

        script_data.setdefault("voice_style", voice_style)
        script_data.setdefault("music_style", music_style)

        # Standardize keywords and prompts
        for s in script_data.get("scenes", []):
            queries = s.get("search_queries", [])
            s["keywords"] = queries or [f"{subject} cute", subject]
            if not s.get("prompt") and character_token:
                s["prompt"] = f"{character_token}, {s.get('visual_action', s.get('text', ''))}, 9:16 vertical, photorealistic, 8k"

        return script_data
