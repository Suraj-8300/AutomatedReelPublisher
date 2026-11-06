"""
AI Script Writer — uses Gemini 2.5 Flash (free tier) to generate viral 3-Act
scripts, scene storyboard prompts, mechanical schematics, and explainer diagrams.
"""

import os
import json
import re
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

from video.config import GEMINI_API_KEY, GEMINI_SCRIPT_MODEL


def _get_client():
    if not _GENAI_AVAILABLE:
        raise ImportError("google-genai not installed. Run: pip install google-genai")
    api_key = GEMINI_API_KEY or os.getenv("AI_STUDIO_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set. Add GEMINI_API_KEY or AI_STUDIO_KEY to your .env file.\n"
            "Get a free key at: https://aistudio.google.com/"
        )
    return genai.Client(api_key=api_key, http_options=dict(api_version="v1beta"))


def _call_gemini(prompt: str, temperature: float = 0.7) -> str:
    """Makes a single Gemini API call with automatic multi-model quota cascading."""
    client = _get_client()
    preferred = GEMINI_SCRIPT_MODEL or "gemini-3.5-flash"
    models_to_try = [preferred, "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
    unique_models = list(dict.fromkeys(models_to_try))

    last_err = None
    for model in unique_models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                )
            )
            return response.text.strip()
        except Exception as e:
            last_err = e
            # Try without response_mime_type on same model
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=4096,
                    )
                )
                return response.text.strip()
            except Exception:
                continue

    raise RuntimeError(f"All Gemini models in cascade failed. Last error: {last_err}")


def _extract_json(text: str) -> Dict:
    """Robustly extracts JSON from a Gemini response that may have markdown fences."""
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {}


class ScriptWriter:
    """
    Generates viral 3-Act scripts and tailored visual storyboard prompts
    using Gemini 2.5 Flash across all 4 content pillars:
    - cinematic: Hyper-cinematic surreal/cosmic visual storytelling
    - science: Breakthrough science news & discovery documentaries
    - mechanical: Internal working of mechanical components with cutaway CAD schematics
    - explainer: Step-by-step educational infographics and scientific diagrams
    """

    @classmethod
    def write_script(cls, topic: str, pillar: str = "science", article_summary: str = "") -> Dict[str, Any]:
        """
        Universal script writer for any content pillar.
        Generates 3-Act viral narration and 3 scene-by-scene diagrammatic or cinematic prompts.
        """
        context = f"\n\nBackground research:\n{article_summary[:800]}" if article_summary else ""

        if pillar in ("animal_story", "storytelling", "cute_animals"):
            system_role = (
                "You are an elite viral storyteller crafting emotional, heartwarming short narrative videos "
                "about cute animals, miraculous rescues, and touching bonds (like The Dodo, GeoBeats, and Love Meow). "
                "Every story follows a profound 3-Act emotional arc: The Vulnerable Hook, The Act of Kindness, and The Joyful Payoff."
            )
            scene_instructions = (
                "For 'scenes', create EXACTLY 3 sequential story scenes where the visuals STRICTLY DEPICT what is spoken:\n"
                "- Scene 1 (The Emotional Hook):\n"
                "  * 'text': 1-2 spoken sentences introducing the cute animal and their fragile struggle (15-20 words).\n"
                "  * 'prompt': Hyper-detailed prompt showing the exact cute animal in that vulnerable situation (30-50 words, 9:16 vertical, soft cinematic lighting, emotional 8k photorealistic portrait).\n"
                "  * 'search_fallback': 2-3 word search query (e.g. 'ginger kitten rain').\n"
                "- Scene 2 (The Turning Point / Kindness):\n"
                "  * 'text': 2 spoken sentences describing how a gentle human arrives, wraps them in warmth, feeds them, and earns their trust (20-25 words).\n"
                "  * 'prompt': Hyper-detailed prompt showing the rescuer and the same animal together in warmth (30-50 words, 9:16 vertical, warm golden lighting, photorealistic).\n"
                "  * 'search_fallback': 2-3 word search query (e.g. 'baker holding kitten').\n"
                "- Scene 3 (The Triumphant Payoff):\n"
                "  * 'text': 1-2 spoken sentences delivering the heartwarming payoff of their happy life today (15-20 words).\n"
                "  * 'prompt': Hyper-detailed prompt showing the grown, happy, fluffy animal thriving in their forever home (30-50 words, 9:16 vertical, golden sunbeams, joyful photorealistic).\n"
                "  * 'search_fallback': 2-3 word search query (e.g. 'happy ginger cat').\n"
                "CRITICAL: Maintain the exact same animal appearance (breed, color, markings) across all 3 prompts!"
            )
            voice_default = "female"
            music_default = "heartwarming_story"

        elif pillar == "mechanical":
            system_role = (
                "You are an elite mechanical engineering communicator creating viral 9:16 vertical "
                "explainer reels (like Engineering Explained / Veritasium). You explain the internal "
                "physics and mechanical components step-by-step using 3D cutaways and CAD schematics."
            )
            scene_instructions = (
                "For 'scenes', create 3 scene descriptors showing the INTERNAL MECHANICAL WORKING:\n"
                "- Scene 1: Intake / primary mechanism cutaway schematic with labeled airflow/fluid/pressure vectors.\n"
                "  * 'text': Opening spoken hook explaining what this machine achieves.\n"
                "  * 'prompt': Technical CAD blueprint cutaway of primary intake mechanism, 9:16 vertical.\n"
                "  * 'search_fallback': 2-3 word search query.\n"
                "- Scene 2: Internal combustion / compression / core gear interaction showing internal parts moving.\n"
                "  * 'text': Spoken explanation of the internal mechanical cycle.\n"
                "  * 'prompt': Cross-section schematic of compression chamber and moving gears, 9:16 vertical.\n"
                "  * 'search_fallback': 2-3 word search query.\n"
                "- Scene 3: Power output / exhaust / kinetic delivery schematic showing the mechanical payoff.\n"
                "  * 'text': Spoken payoff explaining total horsepower or thrust output.\n"
                "  * 'prompt': Exploded 3D CAD schematic of drive assembly, 9:16 vertical.\n"
                "  * 'search_fallback': 2-3 word search query.\n"
                "All prompts MUST describe an engineering cutaway blueprint / CAD schematic, photorealistic, 9:16 vertical."
            )
            voice_default = "british"
            music_default = "cyber_pulse"

        elif pillar == "explainer":
            system_role = (
                "You are an expert scientific visualizer (like 3Blue1Brown / Kurzgesagt). "
                "You explain complex physics, mathematical formulas, algorithms, or natural laws "
                "with clear diagrammatic and conceptual infographics."
            )
            scene_instructions = (
                "For 'scenes', create 3 scene descriptors showing DIAGRAMMATIC EXPLANATIONS:\n"
                "- Scene 1: The foundational problem or question visualized as an elegant dark-mode infographic.\n"
                "- Scene 2: The step-by-step mechanics / mathematical transition with glowing visual vectors.\n"
                "- Scene 3: The mind-bending payoff / final concept visualization.\n"
                "Each scene MUST include 'text' (spoken sentence), 'prompt' (visual description), and 'search_fallback'."
            )
            voice_default = "documentary"
            music_default = "curiosity_lofi"

        elif pillar == "cinematic":
            system_role = (
                "You are an elite viral cosmic and sci-fi storyteller creating hyper-cinematic "
                "vertical reels for YouTube Shorts and Instagram Reels."
            )
            scene_instructions = (
                "For 'scenes', create 3 hyper-detailed, photorealistic cinematic image prompts:\n"
                "- Scene 1: Dramatic opening visual that stops thumb-scrolling instantly.\n"
                "- Scene 2: Close-up intense detail of the phenomenon with volumetric lighting.\n"
                "- Scene 3: Epic scale, awe-inspiring wide shot.\n"
                "Each scene MUST include 'text' (spoken sentence), 'prompt' (visual description), and 'search_fallback'."
            )
            voice_default = "dark_mystery"
            music_default = "deep_mystery"

        else:  # science
            system_role = (
                "You are a top science documentary narrator covering breaking scientific discoveries, "
                "space exploration, biotechnology, and physics breakthroughs."
            )
            scene_instructions = (
                "For 'scenes', create 3 scene descriptors showing the scientific discovery:\n"
                "- Scene 1: The mysterious observation or groundbreaking laboratory setup.\n"
                "- Scene 2: Microscopic or telescopic detail of the discovery in action.\n"
                "- Scene 3: The world-changing impact visualized.\n"
                "Each scene MUST include 'text' (spoken sentence), 'prompt' (visual description), and 'search_fallback'."
            )
            voice_default = "documentary"
            music_default = "ambient_glow"

        prompt = f"""{system_role}

Topic: {topic}{context}
Pillar: {pillar}

Write a high-retention 25-35 second script formatted for vertical video.
{scene_instructions}

Return ONLY valid JSON in this exact structure:
{{
  "title": "Short catchy title (max 6 words)",
  "hook": "Single jaw-dropping opening sentence (max 15 words) that immediately grabs attention.",
  "escalation": "2-3 sentences explaining the journey, inner workings, or surprising facts.",
  "payoff": "1-2 sentences delivering the emotional or satisfying payoff.",
  "voice_style": "{voice_default}",
  "music_style": "{music_default}",
  "scenes": [
    {{
      "scene_num": 1,
      "text": "Exact spoken narration for scene 1 (15-20 words)",
      "prompt": "Detailed visual prompt describing EXACTLY what is spoken in this scene (30-50 words), 9:16 vertical, photorealistic, 8k",
      "search_fallback": "2-3 words for photo search (e.g. orange kitten rain)",
      "keywords": ["2-3 stock video keywords", "e.g. kitten", "rain"]
    }},
    {{
      "scene_num": 2,
      "text": "Exact spoken narration for scene 2 (20-25 words)",
      "prompt": "Detailed visual prompt describing EXACTLY what is spoken in this scene (30-50 words), 9:16 vertical, photorealistic, 8k",
      "search_fallback": "2-3 words for photo search",
      "keywords": ["2-3 stock video keywords", "e.g. baker", "kitchen"]
    }},
    {{
      "scene_num": 3,
      "text": "Exact spoken narration for scene 3 (15-20 words)",
      "prompt": "Detailed visual prompt describing EXACTLY what is spoken in this scene (30-50 words), 9:16 vertical, photorealistic, 8k",
      "search_fallback": "2-3 words for photo search",
      "keywords": ["2-3 stock video keywords", "e.g. cat", "happy"]
    }}
  ]
}}
"""
        raw = _call_gemini(prompt)
        result = _extract_json(raw)

        # Fallbacks for missing keys
        result.setdefault("voice_style", voice_default)
        result.setdefault("music_style", music_default)

        # Assemble full narration from scenes if provided
        scenes = result.get("scenes", [])
        if scenes:
            scene_texts = [s.get("text", "").strip() for s in scenes if s.get("text")]
            if scene_texts and len(scene_texts) == len(scenes):
                result["narration"] = " ".join(scene_texts)

        if not result.get("narration"):
            hook = result.get("hook", "").strip()
            escalation = result.get("escalation", "").strip()
            payoff = result.get("payoff", "").strip()
            result["narration"] = f"{hook} {escalation} {payoff}".strip()

        # Ensure every scene has text, prompt, and search_fallback
        if not scenes:
            scenes = [
                {"scene_num": 1, "text": result.get("hook", f"Discover the story of {topic}."), "prompt": f"Dramatic photorealistic portrait of {topic}, 9:16 vertical, 8k", "search_fallback": topic[:20]},
                {"scene_num": 2, "text": result.get("escalation", "Step by step, the journey unfolds with unexpected depth."), "prompt": f"Detailed cinematic close-up of {topic} in action, volumetric lighting, 9:16 vertical", "search_fallback": topic[:20]},
                {"scene_num": 3, "text": result.get("payoff", "A powerful reminder of what is possible."), "prompt": f"Epic wide shot of {topic}, golden hour radiant lighting, 9:16 vertical", "search_fallback": topic[:20]},
            ]
            result["scenes"] = scenes
        else:
            # Ensure text is present on all scenes
            if not scenes[0].get("text") and result.get("hook"):
                scenes[0]["text"] = result.get("hook")
            if len(scenes) > 1 and not scenes[1].get("text") and result.get("escalation"):
                scenes[1]["text"] = result.get("escalation")
            if len(scenes) > 2 and not scenes[2].get("text") and result.get("payoff"):
                scenes[2]["text"] = result.get("payoff")

        return result

    # Backwards compatibility methods
    @classmethod
    def write_cinematic_script(cls, topic: str, article_summary: str = "") -> Dict[str, Any]:
        return cls.write_script(topic, pillar="cinematic", article_summary=article_summary)

    @classmethod
    def write_manim_code(cls, topic: str, pillar: str) -> Dict[str, Any]:
        # Also returns full scene prompts so visuals never fail if Manim is missing
        script = cls.write_script(topic, pillar=pillar)
        script["scene_class"] = "AutoReelScene"
        script["manim_code"] = cls._fallback_manim_code(topic, pillar)
        return script

    @staticmethod
    def _fallback_manim_code(topic: str, pillar: str) -> str:
        safe_topic = topic.replace('"', "'")
        return f'''from manim import *

config.frame_width = 6
config.frame_height = 10.67

class AutoReelScene(Scene):
    def construct(self):
        self.camera.background_color = "#0a0a0f"
        title = Text("{safe_topic[:45]}", font_size=40, color=WHITE, weight=BOLD)
        title.set_width(5.5)
        title.move_to(UP * 3)
        line = Line(LEFT * 2.5, RIGHT * 2.5, color=BLUE, stroke_width=3)
        line.next_to(title, DOWN, buff=0.3)
        body = Text("Exploring the mechanics\\nand internal working.", font_size=32, color=LIGHT_GRAY)
        body.move_to(ORIGIN)
        self.play(FadeIn(title), Create(line), run_time=1.2)
        self.play(Write(body), run_time=2.0)
        self.wait(2)
'''
