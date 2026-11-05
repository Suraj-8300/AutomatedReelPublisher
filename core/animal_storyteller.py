import random
from typing import Dict, Any, List, Optional
from .character_director import CharacterDirector, ANIMAL_SPECIES, UNUSUAL_DUOS

# ==============================================================================
# VISUAL STYLES SPECIFICATION
# ==============================================================================
VISUAL_STYLES = {
    "photorealistic": {
        "label": "Photorealistic Animals",
        "description": "Ultra-realistic fur, natural lighting, cinematic depth of field, real environment",
        "prompt_prefix": "cinematic hyper-realistic animal photography, National Geographic 8k, ultra-detailed fur texture and whiskers, natural volumetric sunlight, shallow depth of field, award-winning shot, 9:16 vertical aspect ratio",
        "negative_prompt": "cartoon, 3d render, illustration, bad anatomy, deformed, extra limbs, plastic, blurry, watermark, borders"
    },
    "pixar_3d": {
        "label": "Pixar-Inspired 3D Animation",
        "description": "Adorable 3D stylized character, oversized expressive glassy eyes, Disney/Pixar look, soft lighting",
        "prompt_prefix": "stunning 3D animated film still, Disney Pixar 3D art style, adorable character design, giant expressive glossy eyes, soft subsurface scattering fur, warm golden hour rim lighting, rendered in Octane Render, 9:16 vertical aspect ratio",
        "negative_prompt": "live action photograph, flat 2d, creepy, deformed paws, distorted face, ugly, watermark, black borders"
    },
    "cartoon_2d": {
        "label": "2D Cartoon Animation",
        "description": "Vibrant hand-drawn animation, cel-shading, colorful whimsical storybook world",
        "prompt_prefix": "classic 2D animation, vibrant hand-drawn cel animation, colorful whimsical storybook illustration, clean ink lineart, Studio Ghibli inspired cozy aesthetic, expressive happy character, 9:16 vertical aspect ratio",
        "negative_prompt": "photorealistic, 3d render, gritty, dark, distorted, blurry, watermark"
    },
    "anime": {
        "label": "Anime-Inspired Animation",
        "description": "Makoto Shinkai aesthetic, gorgeous painted background, magical golden lighting",
        "prompt_prefix": "beautiful anime visual style, Makoto Shinkai aesthetic, gorgeous painted background, magical golden lighting, expressive anime animal eyes, cinematic anime keyframe, 9:16 vertical aspect ratio",
        "negative_prompt": "western cartoon, live action, lowres, extra limbs, ugly, watermark"
    },
    "stop_motion": {
        "label": "Handcrafted Stop-Motion",
        "description": "Miniature felted wool and clay sculpture, macro photography, cozy dollhouse set",
        "prompt_prefix": "handcrafted stop-motion animation, miniature felted wool and clay sculpture, macro photography, shallow depth of field, cozy tactile textures, handcrafted miniature dollhouse diorama set, Aardman inspired, 9:16 vertical aspect ratio",
        "negative_prompt": "cgi, 2d cartoon, flat, digital drawing, low quality, watermark"
    },
    "fantasy_world": {
        "label": "Fantasy & Magical World",
        "description": "Bioluminescent fairy forest, floating sky islands, enchanted miniature village",
        "prompt_prefix": "enchanted fairytale fantasy world, magical glowing flora, ethereal bioluminescent forest, sparkling fairy dust, dreamy pastel mist, cinematic whimsical fantasy adventure, 9:16 vertical aspect ratio",
        "negative_prompt": "modern city, realistic street, gritty, dark horror, lowres, watermark"
    }
}

# ==============================================================================
# HUMAN-LIKE ANIMAL ACTIVITIES & SETTINGS
# ==============================================================================
ACTIVITIES = {
    "baking_pancakes": {
        "label": "Making Breakfast Pancakes",
        "location": "a sunlit miniature kitchen with pastel tiles and wooden shelves",
        "props": "a tiny cast-iron skillet, bowl of golden batter, small jar of honey and blueberries",
        "action_start": "wearing a tiny chef hat and carefully whisking batter in a mini bowl",
        "action_twist": "flipping a pancake with all its strength; it lands right on its nose",
        "action_payoff": "stacking four golden mini pancakes drizzled with sweet honey, licking lips happily"
    },
    "running_bakery": {
        "label": "Opening a Tiny Village Bakery",
        "location": "a cozy cobblestone storefront with a warm glowing display window",
        "props": "miniature wooden counter, trays of warm croissants and strawberry tarts, small brass bell",
        "action_start": "sweeping the front doorstep and proudly hanging the Open sign with two paws",
        "action_twist": "a sudden rush of forest animal customers arrives, filling the shop with happy chatter",
        "action_payoff": "handing out fresh warm pastries and celebrating a bustling first day"
    },
    "camping_adventure": {
        "label": "Camping Under the Stars",
        "location": "a mossy pine forest clearing with a view of a starry mountain peak",
        "props": "a tiny plaid tent, miniature camp lantern, roasting stick with mini marshmallow",
        "action_start": "rolling out a sleeping bag inside the cozy tent and unzipping the doorway",
        "action_twist": "hearing curious rustling outside; peering out to see a firefly glowing brightly",
        "action_payoff": "toasting marshmallows under the Milky Way and snuggling into the sleeping bag"
    },
    "driving_mini_car": {
        "label": "Cruising in a Tiny Vehicle",
        "location": "a winding garden pathway lined with giant colorful tulips and pebbles",
        "props": "a vintage miniature red toy convertible with shiny chrome wheels and checkered flag",
        "action_start": "wearing tiny aviator goggles and putting both paws firmly on the steering wheel",
        "action_twist": "navigating a tricky turn around a sleeping garden snail, honking a tiny horn",
        "action_payoff": "zooming across the finish line with ears flying back in pure joy"
    },
    "birthday_surprise": {
        "label": "Preparing a Surprise Birthday",
        "location": "a festive living room decorated with colorful pastel bunting and paper streamers",
        "props": "a tiered carrot and berry cake with a single glowing candle, party hats, gift box with yellow ribbon",
        "action_start": "hiding behind a cozy armchair while balancing a birthday cake carefully",
        "action_twist": "jumping out with confetti as the best friend walks through the door in shock",
        "action_payoff": "sharing a warm hug, blowing out the candle, and eating the first delicious slice"
    },
    "secret_garden_quest": {
        "label": "Discovering a Mysterious Secret Door",
        "location": "an ancient ivy-covered stone wall at the edge of an old apple orchard",
        "props": "a glowing brass key on a ribbon, a miniature lantern, ancient arched wooden door",
        "action_start": "brushing aside thick emerald ivy leaves to reveal an ancient keyhole",
        "action_twist": "turning the key with a soft golden click as the door slowly creaks open",
        "action_payoff": "stepping into a sunlit wonderland filled with blooming giant glowing clover"
    },
    "tiny_office_day": {
        "label": "Working at a Miniature Office",
        "location": "a tiny modern corner office with a miniature desk and small houseplant",
        "props": "a matchbox-sized laptop with glowing screen, small cup of coffee, yellow sticky notes",
        "action_start": "adjusting round glasses and tapping tiny paws rapidly on the keyboard",
        "action_twist": "reaching for coffee but accidentally spilling paperclips into a neat pile",
        "action_payoff": "closing the laptop at 5 PM with a satisfied sigh and stretching into a nap"
    },
    "rescue_and_friendship": {
        "label": "Rescuing a Lost Friend in the Rain",
        "location": "a puddle-strewn cobblestone lane under soft April rain",
        "props": "a large green leaf used as an umbrella, warm woolen blanket, cup of warm broth",
        "action_start": "hearing a gentle whimper and finding a lost tiny shivering friend by the doorstep",
        "action_twist": "holding the leaf umbrella over the friend and gently guiding them inside",
        "action_payoff": "sharing a warm fireplace and blanket together, becoming inseparable best friends"
    }
}

# ==============================================================================
# STORY TEMPLATES & ARCHETYPES
# ==============================================================================
STORY_ARCHETYPES = {
    "funny": {
        "themes": ["kitchen_chaos", "clumsy_heist", "ambitious_scheme"],
        "music_style": "playful_bounce",
        "narrator_tone": "humorous and playful",
        "pacing": "energetic"
    },
    "cute": {
        "themes": ["friendship_bond", "first_steps", "cuddle_time"],
        "music_style": "cozy_acoustic",
        "narrator_tone": "gentle and heartwarming",
        "pacing": "tender"
    },
    "adventure": {
        "themes": ["treasure_hunt", "uncharted_forest", "brave_journey"],
        "music_style": "cinematic_adventure",
        "narrator_tone": "epic and curious",
        "pacing": "dynamic"
    },
    "emotional": {
        "themes": ["unconditional_loyalty", "finding_a_home", "protective_bond"],
        "music_style": "cozy_acoustic",
        "narrator_tone": "deeply touching and sweet",
        "pacing": "slow and emotional"
    },
    "unexpected_funny": {
        "themes": ["absurd_profession", "animal_ceo", "secret_life"],
        "music_style": "playful_bounce",
        "narrator_tone": "witty deadpan",
        "pacing": "fast with comedic beats"
    },
    "educational": {
        "themes": ["nature_wonders", "how_things_work", "seasonal_changes"],
        "music_style": "magical_fantasy",
        "narrator_tone": "fascinating and clear",
        "pacing": "informative and joyful"
    }
}

class AnimalStoryteller:
    """
    Generates rich, character-consistent, scene-by-scene narrative scripts
    and complete cinematography storyboards for AI animal filmmaking.
    """

    @staticmethod
    def generate_story(
        animal_species: Optional[str] = None,
        is_duo: bool = False,
        visual_style: Optional[str] = None,
        story_genre: Optional[str] = None,
        activity_type: Optional[str] = None,
        duration: int = 15,
        custom_concept: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Creates a complete cinematic animal story with character sheets & scene breakdown."""
        rng = random.Random(seed) if seed is not None else random.Random()

        # 1. Resolve Visual Style
        if not visual_style or visual_style not in VISUAL_STYLES:
            visual_style = rng.choice(list(VISUAL_STYLES.keys()))
        style_meta = VISUAL_STYLES[visual_style]

        # 2. Resolve Character / Duo
        if is_duo or (custom_concept and any(w in custom_concept.lower() for w in ["and", "duo", "friends", "together"])):
            char_data = CharacterDirector.create_duo_profile(seed=seed)
            main_character_desc = char_data["combined_prompt_signature"]
            hero_name = f"{char_data['character_1']['name']} & {char_data['character_2']['name']}"
            hero_species = f"{char_data['character_1']['species']} and {char_data['character_2']['species']}"
        else:
            char_profile = CharacterDirector.create_character_profile(species=animal_species, seed=seed)
            char_data = {"is_duo": False, "character": char_profile}
            main_character_desc = char_profile["prompt_signature"]
            hero_name = char_profile["name"]
            hero_species = char_profile["species"]

        # 3. Resolve Story Genre & Activity
        if not story_genre or story_genre not in STORY_ARCHETYPES:
            story_genre = rng.choice(list(STORY_ARCHETYPES.keys()))
        genre_meta = STORY_ARCHETYPES[story_genre]

        if not activity_type or activity_type not in ACTIVITIES:
            # Match activity intelligently to genre
            if story_genre in ["funny", "unexpected_funny"]:
                activity_type = rng.choice(["baking_pancakes", "driving_mini_car", "tiny_office_day", "running_bakery"])
            elif story_genre in ["cute", "emotional"]:
                activity_type = rng.choice(["birthday_surprise", "rescue_and_friendship", "camping_adventure"])
            else:
                activity_type = rng.choice(list(ACTIVITIES.keys()))
        act_meta = ACTIVITIES[activity_type]

        # 4. Construct Scene Breakdown (3 scenes for 15s, 4 scenes for 30s, 6 scenes for 60s)
        num_scenes = 3 if duration <= 15 else (4 if duration <= 30 else 5)
        scene_duration = round(duration / num_scenes, 1)

        scenes = AnimalStoryteller._build_scenes(
            char_data=char_data,
            hero_name=hero_name,
            hero_species=hero_species,
            activity=act_meta,
            style=style_meta,
            genre=story_genre,
            num_scenes=num_scenes,
            scene_duration=scene_duration,
            custom_concept=custom_concept,
            rng=rng
        )

        full_script = " ".join(s["dialogue_or_narration"] for s in scenes)
        title = f"{hero_name}'s {act_meta['label']}"
        if custom_concept:
            title = custom_concept.strip().rstrip(".?!").capitalize()

        return {
            "title": title,
            "character_data": char_data,
            "hero_name": hero_name,
            "hero_species": hero_species,
            "visual_style": visual_style,
            "style_meta": style_meta,
            "story_genre": story_genre,
            "activity_type": activity_type,
            "target_duration": duration,
            "music_style": genre_meta["music_style"],
            "script": full_script,
            "scenes": scenes,
            "hook": scenes[0]["dialogue_or_narration"],
            "is_animal_story": True,
            "genre": "storytelling",
            "subgenre": f"Animal Cinema • {style_meta['label']}",
            "visual_approach": visual_style,
            "voice": "en-US-JennyNeural" if story_genre in ["cute", "emotional", "adventure"] else "en-US-GuyNeural",
            "speech_rate": "-2%",
            "caption_style": "cinematic",
            "theme": "cozy_warm" if visual_style in ["photorealistic", "pixar_3d", "stop_motion"] else "nature",
            "badge": f"🐾 {hero_name}",
            "keywords": [hero_species.split()[0], "cute", "animal"],
            "seed": seed or 42,
            "source": "AI Animal Filmmaker Studio"
        }

    @staticmethod
    def _build_scenes(
        char_data: Dict[str, Any],
        hero_name: str,
        hero_species: str,
        activity: Dict[str, Any],
        style: Dict[str, Any],
        genre: str,
        num_scenes: int,
        scene_duration: float,
        custom_concept: Optional[str],
        rng: random.Random
    ) -> List[Dict[str, Any]]:
        """Constructs rich film scenes with exact cinematography, action, and AI visual prompts."""
        is_duo = char_data.get("is_duo", False)
        char_prompt = char_data["combined_prompt_signature"] if is_duo else char_data["character"]["prompt_signature"]

        scenes = []

        # SCENE 1: THE HOOK & OPENING (0-3s)
        s1_cam = "medium shot with gentle camera push-in"
        s1_lighting = "warm morning sunlight filtering through kitchen window, cozy rim lighting"
        if is_duo:
            s1_action = f"{hero_name} meeting in {activity['location']}, {activity['action_start']}"
            s1_dialogue = f"Meet {hero_name}. Today, they decided to tackle something truly ambitious: {activity['label'].lower()}."
        else:
            s1_action = f"{hero_name} inside {activity['location']}, {activity['action_start']}"
            s1_dialogue = f"Meet {hero_name}. A tiny {hero_species} with a huge dream: mastering the art of {activity['label'].lower()}."

        s1_prompt = f"{style['prompt_prefix']}, {char_prompt}, {s1_action}, {activity['props']}, {s1_lighting}, {s1_cam}"

        scenes.append({
            "scene_number": 1,
            "duration": scene_duration,
            "location": activity["location"],
            "camera_angle": "Medium Establishing Shot, Slow Push-In",
            "character_action": s1_action,
            "lighting": s1_lighting,
            "sfx": "soft paw patter on floor, gentle clock ticking, cheerful morning birds",
            "dialogue_or_narration": s1_dialogue,
            "ai_visual_prompt": s1_prompt,
            "negative_prompt": style["negative_prompt"],
            "keywords": [hero_species.split()[0], "cute", "kitchen", "morning"]
        })

        # SCENE 2: STORY DEVELOPMENT & COMPLICATION
        s2_cam = "close-up macro shot focusing on expressive eyes and determined paws"
        s2_lighting = "soft focused golden light on character face, shallow depth of field"
        s2_action = f"{hero_name} in the middle of action: {activity['action_twist']}"
        if genre in ["funny", "unexpected_funny"]:
            s2_dialogue = f"Everything was going smoothly, until a sudden burst of enthusiasm turned the entire room into total chaos."
            s2_sfx = "flour poof sound, cartoon slide whistle, comical clatter of pans"
        else:
            s2_dialogue = f"With laser focus and unmatched determination, every single movement was executed with pure heart."
            s2_sfx = "delicate stirring sound, sizzling skillet, sweet happy chirp"

        s2_prompt = f"{style['prompt_prefix']}, {char_prompt}, {s2_action}, dramatic funny expression, {s2_lighting}, {s2_cam}"

        scenes.append({
            "scene_number": 2,
            "duration": scene_duration,
            "location": activity["location"],
            "camera_angle": "Close-Up Macro Shot, Tracking Paws",
            "character_action": s2_action,
            "lighting": s2_lighting,
            "sfx": s2_sfx,
            "dialogue_or_narration": s2_dialogue,
            "ai_visual_prompt": s2_prompt,
            "negative_prompt": style["negative_prompt"],
            "keywords": [hero_species.split()[0], "funny", "action", "close-up"]
        })

        # SCENE 3: PAYOFF & HEARTWARMING RESOLUTION
        s3_cam = "warm medium-wide shot panning gently, framing the final proud achievement"
        s3_lighting = "glowing golden hour sunset light, warm festive ambiance, sparkling dust motes"
        s3_action = f"{hero_name} proudly admiring their finished work: {activity['action_payoff']}"
        if genre in ["funny", "unexpected_funny"]:
            s3_dialogue = f"Against all odds, the mission was a delicious success. The kitchen didn't survive, but the masterpiece was legendary."
            s3_sfx = "cheerful bell chime, contented deep purr, joyful celebration chime"
        elif genre == "cute":
            s3_dialogue = f"Because the best things in life aren't about being perfect — they're about the love you share along the way."
            s3_sfx = "soft warm harp glissando, happy tail wag thumping, gentle sigh"
        else:
            s3_dialogue = f"A legendary victory for one little hero, proving that size never limits the size of your heart."
            s3_sfx = "triumphant warm brass chime, cozy fire crackle, happy snuggle sound"

        s3_prompt = f"{style['prompt_prefix']}, {char_prompt}, {s3_action}, joyful proud smile, {s3_lighting}, {s3_cam}"

        scenes.append({
            "scene_number": 3,
            "duration": scene_duration,
            "location": activity["location"],
            "camera_angle": "Warm Medium-Wide, Gentle Drift Out",
            "character_action": s3_action,
            "lighting": s3_lighting,
            "sfx": s3_sfx,
            "dialogue_or_narration": s3_dialogue,
            "ai_visual_prompt": s3_prompt,
            "negative_prompt": style["negative_prompt"],
            "keywords": [hero_species.split()[0], "happy", "friends", "celebration"]
        })

        # If 4 or 5 scenes requested, add transitional adventure scenes
        if num_scenes >= 4:
            s4_cam = "macro extreme close-up of peaceful sleeping face curled up next to creation"
            s4_lighting = "twilight blue moonlight mixed with soft golden bedside lamp glow"
            s4_action = f"{hero_name} peacefully falling asleep beside the finished project, cozy smile"
            s4_dialogue = f"And as the stars came out, our little hero drifted off to sleep, already dreaming of tomorrow's next big adventure."
            s4_prompt = f"{style['prompt_prefix']}, {char_prompt}, {s4_action}, peaceful sleeping expression, curled up cozy in tiny blanket, {s4_lighting}, {s4_cam}"

            scenes.append({
                "scene_number": 4,
                "duration": scene_duration,
                "location": activity["location"],
                "camera_angle": "Extreme Close-Up, Soft Focus Drift",
                "character_action": s4_action,
                "lighting": s4_lighting,
                "sfx": "rhythmic gentle purring, soft lullaby music box chime",
                "dialogue_or_narration": s4_dialogue,
                "ai_visual_prompt": s4_prompt,
                "negative_prompt": style["negative_prompt"],
                "keywords": [hero_species.split()[0], "sleeping", "cozy", "night"]
            })

        return scenes
