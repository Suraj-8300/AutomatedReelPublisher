"""
UGC Lifestyle & Product Ad Director for AutoReelStudio.

Standardizes end-to-end production of photorealistic, high-retention UGC ad reels:
1. Creator Identity Consistency (persistent facial features, hair, accessories, outfit).
2. Product Fidelity & Verification (accurate packaging, materials, condensation, labels).
3. 6-Beat High-Converting Narrative Architecture:
   - Hook (unexpected statement / curiosity question)
   - Product Reveal (macro hero lighting + condensation)
   - First Impression (creator interaction & bottle inspection)
   - Opening (cap pop + audio fizz sensory trigger)
   - First Sip (authentic reaction & genuine smile)
   - Product Hero & CTA (hero shot + memorable punchline)
4. Production-Grade Assets:
   - Complete spoken script & word-level timing
   - Shot-by-shot visual generation prompts with strict consistency tokens
   - Sound design & Foley SFX cues
   - Editing, pacing, and on-screen caption styling
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from video.config import OUTPUT_DIR, CACHE_DIR


DEFAULT_CREATOR = {
    "id": "female_pastel_creator",
    "name": "Elena",
    "demographic": "Friendly-looking female creator, early 20s",
    "hair": "Long dark brunette wavy hair falling over shoulders",
    "accessory": "Cute pastel-pink hair clip on the left side of hair",
    "outfit": "Pastel-pink ribbed crop top or relaxed pastel-pink linen summer shirt",
    "facial_features": "Warm hazel-brown eyes, natural approachable smile, subtle summer glow makeup, authentic relatable expressions",
    "consistency_token": (
        "photorealistic 22yo female creator named Elena with long dark brunette wavy hair, "
        "wearing a pastel-pink hair clip on the left and a pastel-pink casual summer outfit, "
        "friendly natural expression, warm summer lighting"
    )
}

DEFAULT_PRODUCT = {
    "brand": "SOLPOPA",
    "flavor": "Mango Soda",
    "packaging_type": "glass_bottle",  # Explicit distinction: NOT a tumbler
    "bottle_description": (
        "Clear contoured glass soda bottle filled with sparkling golden-amber mango soda, "
        "visible fine carbonation bubbles, chilled with fresh condensation droplets glistening on the glass, "
        "vibrant retro-modern SOLPOPA label with fresh mango illustration, sealed with a classic metal crown cap"
    ),
    "consistency_token": (
        "SOLPOPA brand Mango Soda in an authentic clear glass bottle (not a tumbler), "
        "vibrant golden sparkling soda liquid, chilled condensation drops, branded SOLPOPA label, metal bottle cap"
    )
}


class UGCDirector:
    """
    Directs UGC video generation, character/product fidelity, and shot-by-shot production blueprints.
    """

    @classmethod
    def create_solpopa_blueprint(
        cls,
        creator: Optional[Dict[str, Any]] = None,
        product: Optional[Dict[str, Any]] = None,
        concept_hook: str = "Wait… mango soda actually tastes like this?"
    ) -> Dict[str, Any]:
        """
        Builds the complete master production blueprint for the SOLPOPA Mango Soda UGC Reel.
        """
        c = creator or DEFAULT_CREATOR
        p = product or DEFAULT_PRODUCT

        c_token = c["consistency_token"]
        p_token = p["consistency_token"]

        scenes = [
            {
                "scene_num": 1,
                "beat_name": "Hook",
                "start_sec": 0.0,
                "end_sec": 4.5,
                "duration_sec": 4.5,
                "framing": "Medium Close-Up (35mm f/2.0), eye-level selfie angle",
                "spoken_dialogue": "Wait… does mango soda actually taste like this, or have we all been lied to?",
                "on_screen_text": "WAIT… mango soda tastes like THIS?! 🥭🤯",
                "text_style": "Bold yellow & white pop font, centered upper third, gentle bounce entrance",
                "action": (
                    f"{c['name']} holding an unopened chilled {p['brand']} glass bottle slightly out of focus, "
                    "looking directly into camera with an authentic, intrigued eyebrow raise and curiosity expression."
                ),
                "visual_prompt": (
                    f"A vertical 9:16 authentic UGC smartphone video shot of a {c_token}, "
                    f"holding a cold {p_token} in her hand. "
                    "Relatable influencer style, warm afternoon golden hour sunlight through a kitchen window, "
                    "natural room blur bokeh, photorealistic, 8k raw smartphone video texture, hyper-detailed skin texture, "
                    "candid natural expression of disbelief and curiosity."
                ),
                "sfx": "[SFX: Soft acoustic pop music swell, subtle ambient kitchen room tone]",
                "edit_direction": "Quick hook cut (0:00 - 0:04.5), fast dynamic zoom at second 0:02"
            },
            {
                "scene_num": 2,
                "beat_name": "Product Reveal",
                "start_sec": 4.5,
                "end_sec": 9.0,
                "duration_sec": 4.5,
                "framing": "Macro Close-Up (85mm f/2.8), low angle tilt-up hero shot",
                "spoken_dialogue": "I finally found SOLPOPA Mango Soda in the original glass bottle, and look at that color.",
                "on_screen_text": "Real Alphonso Mango 🥭✨ (In Glass!)",
                "text_style": "Clean white subtitle with gold pill highlight, bottom third safe zone",
                "action": (
                    f"Crisp cinematic hero shot of the cold {p['brand']} glass bottle resting on a sunlit marble countertop. "
                    "Golden sunlight illuminating the amber-orange bubbles through the glass, condensation droplets slowly dripping."
                ),
                "visual_prompt": (
                    f"A vertical 9:16 macro hero shot of a {p_token} standing upright on a sun-drenched kitchen marble counter. "
                    "Glistening water condensation drops running down the cold glass surface, glowing golden amber carbonation bubbles, "
                    "warm summer sun flare illuminating the label, sharp focus on the glass texture and bottle neck, shallow depth of field, 8k cinema quality."
                ),
                "sfx": "[SFX: Glass bottle clink on marble, sparkling effervescent fizz ambient sound]",
                "edit_direction": "Speed-ramp glide into the bottle label, smooth pan across condensation"
            },
            {
                "scene_num": 3,
                "beat_name": "First Impression & Inspection",
                "start_sec": 9.0,
                "end_sec": 13.5,
                "duration_sec": 4.5,
                "framing": "Medium Portrait (50mm f/1.8), chest-up",
                "spoken_dialogue": "It's made with real mango puree and sparkling water. No artificial neon syrup.",
                "on_screen_text": "Real Mango Puree • Zero Fake Syrup 🚫",
                "text_style": "Punchy checklist graphic with green checkmarks appearing on beat",
                "action": (
                    f"{c['name']} smiling as she inspects the bottle label, turning the glass bottle smoothly "
                    "to reveal the clean ingredients to the camera."
                ),
                "visual_prompt": (
                    f"Vertical 9:16 shot of the {c_token}, "
                    f"admiringly turning a {p_token} in her hands. "
                    "Genuine, approachable smile, warm daylight filling the cozy modern kitchen, "
                    "crisp focus on creator's hand and the bottle label, authentic UGC creator lighting."
                ),
                "sfx": "[SFX: Upbeat rhythmic drum kicks in, soft vinyl whoosh on bottle turn]",
                "edit_direction": "Punch cut on 'real mango puree' to creator's nodding head"
            },
            {
                "scene_num": 4,
                "beat_name": "Opening & Fizz",
                "start_sec": 13.5,
                "end_sec": 18.0,
                "duration_sec": 4.5,
                "framing": "Extreme Close-Up (100mm macro), bottle neck & cap",
                "spoken_dialogue": "Listen to this pop. That's serious carbonation.",
                "on_screen_text": "🔊 TURN SOUND UP! That fizz… 🍾💥",
                "text_style": "Pulsing audio visualizer emoji icon with bold yellow caption",
                "action": (
                    "Hands lifting bottle opener, popping the silver metal bottle cap off the glass rim. "
                    "Crisp audible hiss, delicate micro-mist of carbonation escaping the bottle lip."
                ),
                "visual_prompt": (
                    f"Vertical 9:16 extreme macro close-up of opening a {p_token}. "
                    "A metal bottle opener levering off the metal crown bottle cap, capturing the exact instant of cap release. "
                    "Visible fine vapor mist puffing out from the bottle neck, golden liquid fizzing with vigorous micro-bubbles, "
                    "crystal-clear focus on condensation beads on glass rim, cinematic 120fps slow-motion feel."
                ),
                "sfx": "[SFX: LOUD crisp metallic bottle cap POP, followed immediately by sharp, satisfying effervescent HISS / FIZZ (ASMR clarity)]",
                "edit_direction": "Audio ducking: background music drops 90% for 1.2s to spotlight the pure ASMR pop & fizz"
            },
            {
                "scene_num": 5,
                "beat_name": "First Sip & Reaction",
                "start_sec": 18.0,
                "end_sec": 23.5,
                "duration_sec": 5.5,
                "framing": "Close-Up Face & Bottle (50mm f/1.8), front angle",
                "spoken_dialogue": "Oh wow… That is crisp, sweet, and actually tastes like a juicy ripe mango. Not candy.",
                "on_screen_text": "OH WOW. 10/10 TASTES LIKE FRESH MANGO 🥭🤤",
                "text_style": "Golden star rating graphic popping in, bold white text with black outline",
                "action": (
                    f"{c['name']} takes a refreshing first sip straight from the cold glass bottle. "
                    "Her eyes widen in genuine delightful surprise, followed by an involuntary happy smile and nod at camera."
                ),
                "visual_prompt": (
                    f"Vertical 9:16 candid UGC close-up of {c_token} taking a refreshing sip from the {p_token}. "
                    "Her eyes widen in spontaneous authentic delight, swallowing and breaking into a genuine, beaming smile. "
                    "Warm summer sunbeams, glistening lips, authentic unforced facial expressions, relatable creator energy, 8k raw portrait."
                ),
                "sfx": "[SFX: Subtle crisp gulp sound, triumphant bright music swell, gentle sparkle sound effect]",
                "edit_direction": "Zoom punch-in at the exact moment of eye-widening surprise"
            },
            {
                "scene_num": 6,
                "beat_name": "Product Hero & Call to Action",
                "start_sec": 23.5,
                "end_sec": 28.5,
                "duration_sec": 5.0,
                "framing": "Medium Selfie with Product Hero (35mm f/2.0)",
                "spoken_dialogue": "If you see SOLPOPA Mango Soda in the glass bottle, grab three. You will thank me later.",
                "on_screen_text": "Run, don't walk. 🏃‍♀️💨 Find SOLPOPA at your local store!",
                "text_style": "High-contrast sticker-style CTA box with animated finger tap pointer",
                "action": (
                    f"{c['name']} holding the cold glass bottle next to her cheek, pointing approvingly at the label, "
                    "giving a knowing nod and warm wink to the camera."
                ),
                "visual_prompt": (
                    f"Vertical 9:16 hero closing shot of {c_token} holding the {p_token} proudly next to her face. "
                    "Smiling warmly into the camera lens with friendly confidence, pointing her finger at the bottle. "
                    "Summer lifestyle background, warm sunlight, photorealistic, authentic TikTok / Instagram creator aesthetic."
                ),
                "sfx": "[SFX: Upbeat musical outro finish, final bright chime on screen tap]",
                "edit_direction": "Subtle slow zoom out, end-card overlay with shop button or handle"
            }
        ]

        full_narration = " ".join([s["spoken_dialogue"] for s in scenes])

        # Standardize scene keys for downstream engines (text, keywords, search_queries)
        for s in scenes:
            s["text"] = s["spoken_dialogue"]
            s["search_queries"] = [
                f"{p['brand']} {p['flavor']}",
                "mango drink glass bottle",
                "opening soda bottle fizz",
                "woman drinking glass bottle",
                "summer drink lifestyle"
            ]
            s["keywords"] = ["mango", "soda", "bottle", "drink"]

        blueprint = {
            "title": "SOLPOPA Mango Soda UGC Lifestyle Ad",
            "topic": "SOLPOPA Mango Soda UGC Lifestyle Ad",
            "narration": full_narration,
            "voice_style": "female",
            "music_style": "upbeat_summer",
            "concept_hook": concept_hook,
            "duration_sec": 28.5,
            "aspect_ratio": "9:16 (1080x1920)",
            "creator_profile": c,
            "product_profile": p,
            "audio_spec": {
                "voice_profile": "female (Ava / Natural English US)",
                "music_profile": "upbeat_summer (Acoustic pop rhythm, warm summer vibes)",
                "music_ducking": "-18dB standard, -24dB during ASMR bottle pop",
                "sfx_count": 6
            },
            "scenes": scenes,
            "full_narration": full_narration,
            "negative_prompts": (
                "tumbler, plastic cup, metal can, bad anatomy, deformed fingers, extra limbs, "
                "blurry face, unnatural waxy skin, cartoon, anime, illustration, CGI, lowres, watermark"
            )
        }

        return blueprint

    @classmethod
    def export_blueprint_files(
        cls,
        blueprint: Dict[str, Any],
        output_prefix: str = "ugc_solpopa_mango"
    ) -> Tuple[Path, Path]:
        """
        Saves the blueprint to disk as both JSON (machine-readable) and Markdown (production brief).
        """
        json_path = OUTPUT_DIR / f"{output_prefix}_blueprint.json"
        md_path = OUTPUT_DIR / f"{output_prefix}_production_brief.md"

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2)

        # Write Markdown Brief
        c = blueprint["creator_profile"]
        p = blueprint["product_profile"]
        scenes = blueprint["scenes"]

        md_content = f"""# 🎬 UGC Video Production Blueprint: {blueprint['title']}

> **Concept:** "{blueprint['concept_hook']}"  
> **Target Format:** 9:16 Vertical Video (1080x1920, 30fps)  
> **Duration:** {blueprint['duration_sec']}s  
> **Production Style:** Photorealistic, authentic lifestyle influencer content, warm summer lighting.

---

## 👤 Creator Identity Consistency Sheet
* **Identity:** {c['demographic']} ({c['name']})
* **Hair:** {c['hair']}
* **Signature Accessory:** {c['accessory']}
* **Wardrobe:** {c['outfit']}
* **Facial & Vibe:** {c['facial_features']}
* **Master Consistency Prompt:**
  `{c['consistency_token']}`

---

## 🍾 Product Verification & Specification
* **Brand & Flavor:** {p['brand']} {p['flavor']}
* **Packaging:** {p['packaging_type'].replace('_', ' ').title()} *(Explicitly NOT a tumbler or can)*
* **Bottle Details:** {p['bottle_description']}
* **Master Consistency Prompt:**
  `{p['consistency_token']}`

---

## 🎞️ Shot-by-Shot Production Breakdown

"""
        for s in scenes:
            md_content += f"""### Shot {s['scene_num']}: {s['beat_name']} ({s['start_sec']}s – {s['end_sec']}s)
* **Framing & Lens:** {s['framing']}
* **Action:** {s['action']}
* **Spoken Narration:** *"{s['spoken_dialogue']}"*
* **On-Screen Text:** **{s['on_screen_text']}** ({s['text_style']})
* **Sound Design & SFX:** `{s['sfx']}`
* **Editing & Transitions:** {s['edit_direction']}
* **AI Visual Generation Prompt:**
```text
{s['visual_prompt']}
```

---
"""

        md_content += f"""## 🎵 Sound Design & Master Audio
* **Voiceover:** {blueprint['audio_spec']['voice_profile']}
* **Background Track:** {blueprint['audio_spec']['music_profile']}
* **Ducking Rules:** {blueprint['audio_spec']['music_ducking']}
* **Negative Prompt:** `{blueprint['negative_prompts']}`
"""

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return json_path, md_path
