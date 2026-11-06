"""
Viral Format Catalog for AutoReelStudio.

Encapsulates the 6 blockbuster AI Reels formats dominating Instagram Reels,
TikTok, and YouTube Shorts:
1. Anthropomorphic Animals (Animals with human jobs: Chef, Waiter, Street Food, Police).
2. AI Babies in Adult Situations (Baby running golgappa stall, Baby podcast, Baby CEO).
3. Surreal Brainrot & Absurd Meme Characters (Tralalero Tralala, Ballerina Cappuccina, Bandar Apna Dost).
4. AI Animal Cinematic Stories (The Abandoned Kitten & Stray Dog, multi-episode recurring heroes).
5. Impossible Satisfying ASMR (Glass fruit slicing, crystal watermelon, seamless kinetic loops).
6. Cinematic POV & Fictional Worlds (POV you wake up in Ancient Rome, Mumbai 2500, Last Human).
"""

from typing import Dict, Any, List, Optional

VIRAL_FORMATS = {
    "anthropomorphic_animal": {
        "title": "AI Animals Behaving Like Humans",
        "description": "Photorealistic animal placed in a serious human job. Contrast between realism and absurdity.",
        "pacing": "Fast 20-30s, 3-act escalation: Uniform reveal -> Overwhelmed chaos -> Boss punchline",
        "voice_style": "british",
        "music_style": "cyber_pulse",
        "templates": [
            {
                "id": "british_cat_waiter",
                "character": "Sophisticated British Shorthair cat wearing a formal black bow tie and waiter waistcoat",
                "setting": "Busy upscale London café during morning rush",
                "hook": "POV: You hired a cat as head waiter and he takes his job way too seriously.",
                "escalation": "Balancing 4 cups of espresso on his paws, meowing sternly at rude customers, accidentally swatting a milk pitcher.",
                "punchline": "The cat manager docks his catnip allowance.",
                "video_prompt": (
                    "Vertical 9:16 cinematic video of a realistic British Shorthair cat wearing a tailored black waiter vest and mini bow tie, "
                    "carefully carrying a tray of espresso cups through a bustling cozy cafe, expressive focused feline eyes, warm morning coffee shop lighting, "
                    "photorealistic, 8k quality, cinematic depth of field."
                )
            },
            {
                "id": "street_food_cat_chef",
                "character": "Fluffy ginger cat wearing a chef apron and headband tossing wok fried rice",
                "setting": "Vibrant night street food stall with glowing neon lanterns",
                "hook": "The best fried rice in Bangkok is made by an orange cat with an anger management problem.",
                "escalation": "Flipping a giant smoking wok with his paws, tossing scallions into the air, glaring at impatient tourists.",
                "punchline": "Charge: 5 head scratches per bowl.",
                "video_prompt": (
                    "Vertical 9:16 photorealistic motion video of a realistic orange tabby cat wearing a tiny white chef bandana and apron, "
                    "skilfully tossing smoking fried rice in a sizzling wok with wok-hei fire flares, night food market atmosphere, steam rising, "
                    "detailed fur texture, vibrant neon street lighting, cinematic 60fps."
                )
            },
            {
                "id": "police_patrol_cat",
                "character": "Stern Maine Coon cat wearing a high-vis police vest and badge",
                "setting": "City street corner on patrol",
                "hook": "Officer Mittens has zero tolerance for jaywalking pigeons.",
                "escalation": "Writing a tiny citation with a paw, radioing dispatch with intense meows, chasing a laser pointer mid-investigation.",
                "punchline": "Case closed: Suspect was bribed with canned tuna.",
                "video_prompt": (
                    "Vertical 9:16 hyperrealistic video of a majestic Maine Coon cat wearing a miniature neon police uniform and gold detective badge, "
                    "sitting alertly next to a police cruiser on a wet rainy city street, reflections in puddles, dramatic cinematic rim lighting."
                )
            }
        ]
    },

    "ai_baby_adult": {
        "title": "AI Babies in Adult Situations",
        "description": "Adorable chubby baby placed into adult professional and cultural roles. Huge reach in Indian short-form.",
        "pacing": "25-30s, deadpan comedic tone, high contrast between cute appearance and mature dialogue",
        "voice_style": "documentary",
        "music_style": "curiosity_lofi",
        "templates": [
            {
                "id": "baby_golgappa_stall",
                "character": "Chubby Indian baby with a kurta and towel over shoulder running a street pani puri stall",
                "setting": "Bustling Mumbai evening street corner with huge puris and stainless steel bowls of spicy mint water",
                "hook": "Sharma ji ka 1-year-old son just launched his third street food franchise.",
                "escalation": "Poking a hole in crispy puris with tiny fingers, measuring spicy teekha water with deadpan precision, scolding aunty for asking for extra sookha puri.",
                "punchline": "'Chutney ke alag se 10 rupaye lagenge, samajh gaye na?'",
                "video_prompt": (
                    "Vertical 9:16 cinematic video of an adorable chubby 1-year-old Indian baby boy wearing a mini kurta and apron, "
                    "confidently serving fresh crispy golgappas at an authentic street food cart, colorful glass jars, fragrant spicy mint water splash, "
                    "warm golden street stall lights, photorealistic facial expressions, lifelike skin texture."
                )
            },
            {
                "id": "baby_podcast",
                "character": "Two chubby babies in oversized tailored business suits sitting in front of professional Shure microphones",
                "setting": "High-end studio with neon purple acoustic wall panels",
                "hook": "Episode 47: Why your baby sleep schedule is destroying your quarterly milk yield.",
                "escalation": "One baby leans into the mic adjusting his gold Rolex, sipping apple juice from a crystal glass, analyzing toddler daycare politics.",
                "punchline": "'Bro, if you're not waking up at 3 AM crying, are you even grinding?'",
                "video_prompt": (
                    "Vertical 9:16 photorealistic studio video of two chubby 10-month-old babies wearing miniature charcoal designer suits, "
                    "sitting at a luxury podcast table speaking into large black studio microphones, neon LED backlight, professional podcast studio depth, "
                    "expressive animated baby faces, hyperrealistic."
                )
            }
        ]
    },

    "brainrot_meme": {
        "title": "Surreal Brainrot & Absurd Meme Characters",
        "description": "Bizarre, impossible character mashups with catchy names, hypnotic soundbites, and viral meme lore.",
        "pacing": "15-25s, sensory overload, rapid meme energy, hypnotic background loop",
        "voice_style": "energetic",
        "music_style": "cyber_pulse",
        "templates": [
            {
                "id": "ballerina_cappuccina",
                "character": "Graceful classical ballerina whose head is an elegant ceramic cappuccino cup with frothy latte art",
                "setting": "Grand classical Italian opera stage under purple stage spotlights",
                "hook": "Meet Ballerina Cappuccina. The most feared prima donna in Milan.",
                "escalation": "Spinning 10 pirouettes without spilling a single drop of steaming espresso foam, dazzling the crowd.",
                "punchline": "Tralalero Tralala challenges her to a duel in Venice.",
                "video_prompt": (
                    "Vertical 9:16 surreal cinematic video of Ballerina Cappuccina: an elegant ballerina wearing a delicate pink tulle tutu "
                    "with a large porcelain cappuccino cup as her head, frothy latte heart art steaming on top, performing graceful pirouettes "
                    "on an ornate Italian theater stage, golden spotlights, surreal masterpiece, 8k render."
                )
            },
            {
                "id": "bandar_hulk_duo",
                "character": "Clever agile monkey wearing traditional waistcoat paired with a gigantic friendly musclebound green beast",
                "setting": "Mystical ancient Indian temple courtyard surrounded by misty banyan trees",
                "hook": "When Bandar Apna Dost finds the enchanted golden banana, even the big guy follows orders.",
                "escalation": "Monkey orchestrating a massive temple challenge while the gentle giant lifts an entire ancient boulder with one finger.",
                "punchline": "Total views: 2.4 Billion. Pure spectacle.",
                "video_prompt": (
                    "Vertical 9:16 epic fantasy video of a clever anthropomorphic macaque monkey wearing an ornate embroidered vest, "
                    "standing shoulder-to-shoulder with a colossal muscular green guardian in front of a mystical stone Indian temple, "
                    "cinematic volumetric fog, cinematic lighting, 8k hyperrealistic character detail."
                )
            }
        ]
    },

    "animal_cinematic_story": {
        "title": "AI Animal Cinematic Stories",
        "description": "Emotional, multi-episode narrative sagas with recurring animal protagonists. High comment & save rates.",
        "pacing": "30-45s, 3-act emotional arc: Heartbreaking vulnerability -> Unexpected cross-species rescue -> Triumphant family bond",
        "voice_style": "female",
        "music_style": "heartwarming_story",
        "templates": [
            {
                "id": "abandoned_kitten_stray_dog",
                "character": "Shivering tiny orange kitten and an old, scarred, gentle stray German Shepherd with a heart of gold",
                "setting": "Rainy city alleyway under cold neon signs transitioning to a warm sheltered dry den",
                "hook": "Left in a cardboard box under the freezing rain, this tiny kitten thought nobody was coming.",
                "escalation": "An old stray dog with a scarred muzzle hears the tiny cry, carefully picks up the kitten by its scruff, and carries it 2 miles to a dry bakery vent.",
                "punchline": "That was two years ago. Today, they are completely inseparable brothers.",
                "video_prompt": (
                    "Vertical 9:16 cinematic video of a gentle, weathered old German Shepherd dog curling protectively around a tiny, "
                    "fluffy orange kitten inside a warm sheltered alley corner, rain pouring outside in the background, warm amber glow from a bakery window, "
                    "deep emotional expression in dog's eyes, photorealistic wet fur textures, cinematic filmic color grade."
                )
            }
        ]
    },

    "impossible_asmr": {
        "title": "Impossible Satisfying ASMR",
        "description": "Hyperrealistic, impossible tactile textures: glass fruits, crystal watermelons, liquid metal slicing with precision Foley sound.",
        "pacing": "15-25s, seamless loop, crisp tactile audio Foley, zero narration needed",
        "voice_style": "documentary",
        "music_style": "ambient_glow",
        "templates": [
            {
                "id": "glass_strawberry_slice",
                "character": "Hand wielding a Damascus steel razor knife slicing a transparent ruby-glass strawberry filled with sparkling liquid",
                "setting": "Pure minimalist dark slate cutting board under focused studio rim light",
                "hook": "Watch what happens when you slice a strawberry made of hand-blown crystal glass.",
                "escalation": "The razor blade glides effortlessly through the translucent ruby glass, releasing miniature crystal seeds and glowing nectar beads.",
                "punchline": "Loop restart: perfectly intact again.",
                "video_prompt": (
                    "Vertical 9:16 ultra-macro 120fps video of a razor-sharp kitchen knife slicing smoothly through a hyperrealistic "
                    "transparent ruby crystal glass strawberry, internal micro-facets refracting light, tiny glass seeds shimmering, "
                    "chilled nectar droplets bursting in slow motion, dark matte slate background, pristine studio macro lighting, 8k photorealistic."
                )
            }
        ]
    },

    "cinematic_pov": {
        "title": "Cinematic POV & Fictional Worlds",
        "description": "First-person perspective transporting the viewer into impossible historical or futuristic worlds.",
        "pacing": "25-35s, immersive sensory worldbuilding, mystery hook",
        "voice_style": "dark_mystery",
        "music_style": "deep_mystery",
        "templates": [
            {
                "id": "pov_mumbai_2500",
                "character": "First-person traveler stepping off a magnetic anti-gravity train above futuristic Mumbai",
                "setting": "Massive vertical bio-skyscrapers entwined with glowing vertical gardens and flying hover-rickshaws",
                "hook": "POV: You just landed in Mumbai in the year 2500.",
                "escalation": "Hovering over the glowing Arabian Sea bridge, flying sky-dhabas serving holographic chai, neon Sanskrit signs soaring into cloud strata.",
                "punchline": "And somehow, the traffic at Dadar station is still 20 minutes delayed.",
                "video_prompt": (
                    "Vertical 9:16 first-person POV shot stepping onto an open-air sky terrace overlooking Mumbai in the year 2500, "
                    "flying hover-vehicles streaming between towering bio-luminescent vertical skyscrapers entwined with exotic hanging gardens, "
                    "golden sunset reflecting off solar glass towers, futuristic Indian aesthetics, cinematic 8k sci-fi worldbuilding."
                )
            }
        ]
    }
}


class ViralFormatCatalog:
    """Provides structured prompts, character bibles, and storyboards for the 6 viral formats."""

    @classmethod
    def list_formats(cls) -> List[str]:
        return list(VIRAL_FORMATS.keys())

    @classmethod
    def get_format(cls, format_id: str) -> Dict[str, Any]:
        return VIRAL_FORMATS.get(format_id, VIRAL_FORMATS["anthropomorphic_animal"])

    @classmethod
    def get_template(cls, format_id: str, template_id: Optional[str] = None) -> Dict[str, Any]:
        fmt = cls.get_format(format_id)
        templates = fmt.get("templates", [])
        if template_id:
            match = next((t for t in templates if t["id"] == template_id), None)
            if match:
                return match
        return templates[0] if templates else {}
