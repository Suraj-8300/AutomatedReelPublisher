"""
Persistent Character Universe & Episodic Continuity Engine for AutoReelStudio.
Implements the 2026 Short-Form Revolution:
- Replaces disconnected random "AI slop" with persistent, recognizable character universes.
- Tracks episodic continuity (Season & Episode numbering, recurring relationships).
- Enforces strict 3-act viral architecture:
    Act 1 (0-4s): Familiar / Absurd Hook
    Act 2 (5-20s): Escalating Chaos / Conflict
    Act 3 (21-28s): Punchline / Heartwarming Payoff
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "universe_state.json"

# ==============================================================================
# CANONICAL CHARACTER UNIVERSES SPECIFICATION
# ==============================================================================

UNIVERSES = {
    "mochi_and_friends": {
        "id": "mochi_and_friends",
        "title": "Mochi & Co. (The Bistro Universe)",
        "category": "animal_universe",
        "description": "A bustling miniature cafe run by a mischievous orange cat and his unlikely animal crew.",
        "cast": [
            {
                "id": "mochi",
                "name": "Mochi",
                "species": "Orange Tabby Cat",
                "traits": "Mischievous, ambitious, emerald eyes, folded ears, tiny white paws, wears a miniature red chef apron",
                "personality": "Chaotic genius, experiments with insane recipes, never admits defeat",
                "visual_token": "a charming photorealistic orange tabby kitten with vibrant emerald green eyes, folded ears, tiny white paws, wearing a crisp red chef apron"
            },
            {
                "id": "barnaby",
                "name": "Barnaby",
                "species": "Old English Bulldog",
                "traits": "Wrinkly face, tiny brass reading glasses perched on nose, tweed vest, holding a mini wooden clipboard",
                "personality": "Strict father figure, sighs constantly, obsessed with hygiene codes, secretly loves Mochi's cooking",
                "visual_token": "a lovable wrinkled old english bulldog wearing round brass reading glasses and a vintage tweed vest, holding a miniature clipboard"
            },
            {
                "id": "pip",
                "name": "Pip",
                "species": "Golden Retriever Puppy",
                "traits": "Oversized clumsy paws, floppy golden ears, teal polka-dot bowtie, wide expressive glossy eyes",
                "personality": "Nervous assistant, easily startled, chief taste-tester, panics when orders stack up",
                "visual_token": "an adorable fluffy golden retriever puppy with giant expressive brown eyes and floppy ears, wearing a teal polka-dot bowtie"
            },
            {
                "id": "luna",
                "name": "Luna",
                "species": "White Lop Bunny",
                "traits": "Velvety snow-white fur, long drooping ears, miniature toolbelt, quick twitching pink nose",
                "personality": "Engineering mastermind, level-headed voice of reason, fixes Mochi's kitchen explosions",
                "visual_token": "a graceful pure-white lop-eared rabbit with soft velvet fur and bright blue eyes, wearing a tiny leather utility toolbelt"
            }
        ],
        "default_voice": "en-US-ChristopherNeural",
        "episodes": [
            {
                "title": "The Pancake Catastrophe",
                "hook": "POV: You let a ginger kitten run Sunday breakfast rush at a Michelin-star cafe.",
                "act1": "Mochi tied his apron tight and cranked the gas stove to maximum. Three hundred hungry woodland critters were banging on the door for pancakes.",
                "act2": "Pip was whisking batter so fast flour covered the ceiling. Mochi attempted a triple-backflip pancake toss — the pancake hit the ceiling fan, spun like a helicopter, and plastered straight across Barnaby's reading glasses.",
                "act3": "Barnaby took off his glasses, took one bite of the pancake stuck to his face, and mumbled: 'Needs more blueberry syrup. Four stars.'",
                "scenes": [
                    {
                        "text": "POV: You let a ginger kitten run Sunday breakfast rush at a Michelin-star cafe.",
                        "visual_prompt": "Cinematic shot of a charming photorealistic orange tabby kitten with emerald green eyes wearing a crisp red chef apron, standing on stool behind miniature cafe counter, morning sunlight streaming through cafe windows, 8k ultra-detailed, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Mochi cranked the stove to max while Pip scrambled with thirty pancake orders, flour flying everywhere as a giant pancake hits the ceiling fan.",
                        "visual_prompt": "Chaotic cute miniature kitchen, fluffy golden retriever puppy covered in white flour looking shocked, while a golden pancake spins off a ceiling fan above, warm cinematic lighting, photorealistic fur, 9:16 vertical",
                        "motion": "pan_left"
                    },
                    {
                        "text": "The pancake landed right on Barnaby's glasses. He took one bite and gave it four stars anyway.",
                        "visual_prompt": "Close-up of a dignified wrinkled old english bulldog with a golden pancake draped over his brass reading glasses, licking sweet maple syrup off his nose with a deadpan expression, 8k cinematic photography, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "acoustic_breeze",
                "soundtrack_genre": "upbeat_comedy"
            },
            {
                "title": "The 100-Order Espresso Rush",
                "hook": "What happens when three cats drink a triple-shot espresso during Monday morning rush?",
                "act1": "At 7:01 AM, the ticket machine started printing orders like a runaway lottery ticker. 142 oat-milk lattes in six minutes.",
                "act2": "Mochi was operating three steam wands simultaneously with both paws and his tail. Pip was carrying five cups balanced on his head like a circus seal, dodging flying milk foam.",
                "act3": "By 7:15 AM, the entire cafe was covered in milk foam art of Barnaby's grumpy face. The customers tipped 50 percent just for the spectacle.",
                "scenes": [
                    {
                        "text": "At 7:01 AM, the ticket machine started spitting orders like a runaway lottery ticker.",
                        "visual_prompt": "Close-up of a vintage brass espresso machine steaming furiously in an artisanal cafe, endless paper orders fluttering down around an orange tabby kitten barista in apron, cinematic lighting, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Mochi operated three steam wands with both paws while Pip balanced five latte cups on his golden head.",
                        "visual_prompt": "Action shot in cozy sunlit cafe, adorable golden retriever puppy balancing miniature porcelain cups on his head while orange kitten steams milk with laser focus, cinematic depth of field, 8k, 9:16 vertical",
                        "motion": "pan_right"
                    },
                    {
                        "text": "The entire room was covered in latte art of Barnaby's face, and the line outside cheered.",
                        "visual_prompt": "Overhead cinematic view of five artisanal lattes with intricate milk foam art depicting a grumpy bulldog face, warm rustic wooden cafe table, photorealistic 8k, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "lofi_chill",
                "soundtrack_genre": "cozy_comedy"
            },
            {
                "title": "The Health Inspector's Surprise Visit",
                "hook": "Barnaby announced a surprise health inspection, and Mochi had 30 seconds to hide the evidence.",
                "act1": "The brass bell chimed. Barnaby stepped in with his white glove and clipboard, clicking his pen with terrifying precision.",
                "act2": "Mochi shoved three stolen salmon fillets into Luna's toolbelt, while Pip stood at attention saluting so hard his floppy ears vibrated. Barnaby wiped the top shelf.",
                "act3": "Barnaby inspected his white glove. Clean. Then Mochi accidentally sneezed a cloud of powdered sugar directly onto Barnaby's shiny black shoes.",
                "scenes": [
                    {
                        "text": "Barnaby announced a surprise health inspection, clicking his pen with terrifying precision.",
                        "visual_prompt": "Dramatic low-angle cinematic shot of a stern wrinkled bulldog inspector in a tweed vest holding a clipboard and clicking a brass pen, ominous lighting, photorealistic 8k, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Mochi shoved secret snacks into rabbit toolbelts while Pip stood at military attention saluting with his paw.",
                        "visual_prompt": "Hilarious contrast shot of an orange tabby kitten frantically hiding a fish behind a flour sack while a golden retriever puppy salutes nervously, warm detailed kitchen, 9:16 vertical",
                        "motion": "pan_left"
                    },
                    {
                        "text": "The kitchen was spotless until Mochi sneezed a cloud of powdered sugar over Barnaby's polished boots.",
                        "visual_prompt": "Slow-motion capture of a fluffy orange kitten mid-sneeze surrounded by a glittering cloud of white powdered sugar settling on black shoes, funny expressive facial details, 8k, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "suspense_comedy"
            },
            {
                "title": "The Secret Pizza Midnight Heist",
                "hook": "POV: You catch your pets running an illegal underground pizzeria at 2 AM.",
                "act1": "At 2:15 AM, the scent of fresh basil and bubbling mozzarella began wafting from the locked pantry door.",
                "act2": "Behind the flour bags, Mochi had built a miniature brick woodfire oven. Luna was calculating dough hydration on a tiny blackboard while Pip rolled pizza dough with a wine bottle.",
                "act3": "When the human opened the pantry door, all three froze. Mochi slowly slid a 3-inch truffle pizza across the floor with a note: 'Five stars or we tell the neighbors.'",
                "scenes": [
                    {
                        "text": "POV: You catch your pets running an underground pizzeria at 2 AM.",
                        "visual_prompt": "Cinematic dark room, ray of light cutting through a cracked wooden pantry door revealing a miniature glowing woodfire pizza oven inside, warm embers glowing, photorealistic 8k, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Mochi was stretching Neapolitan dough while Luna engineered the brick oven chimney with copper pipes.",
                        "visual_prompt": "Intricate miniature pizza workshop, orange tabby kitten tossing tiny pizza dough into the air, white bunny with toolbelt checking heat gauge, glowing firelight, 8k, 9:16 vertical",
                        "motion": "pan_right"
                    },
                    {
                        "text": "They got caught red-pawed and offered a slice as hush money.",
                        "visual_prompt": "Three animal culprits staring wide-eyed up at the camera, tiny kitten paw sliding a perfect miniature steaming pepperoni pizza forward, hilarious expressive eyes, photorealistic 8k, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "mystery_comedy"
            }
        ]
    },

    "baby_boss_ventures": {
        "id": "baby_boss_ventures",
        "title": "Baby Boss Syndicate (Corporate & Street Satire)",
        "category": "baby_comedy",
        "description": "A deadpan 10-month-old CEO in a bespoke three-piece suit tackling corporate politics and street-food empires.",
        "cast": [
            {
                "id": "boss_leo",
                "name": "Leo (The Boss)",
                "species": "Human Infant (10 Months)",
                "traits": "Chubby cheeks, razor-sharp slicked back hair, Italian pinstripe suit, gold baby Rolex, sippy cup labeled 'Q3 REVENUE'",
                "personality": "Deadpan, hyper-articulate boardroom titan, treats teething rings like multi-million dollar asset portfolios",
                "visual_token": "a photorealistic chubby 10-month-old baby with slicked hair wearing a tailored navy pinstripe suit and silk tie, sitting behind a massive mahogany boardroom desk with a studio podcast microphone"
            }
        ],
        "default_voice": "en-US-GuyNeural",
        "episodes": [
            {
                "title": "Baby Boss on Morning Naps vs. EBITDA",
                "hook": "POV: Your 10-month-old calls an emergency 6 AM meeting to renegotiate nap times.",
                "act1": "Leo adjusted his miniature silk tie, cleared his throat into the studio microphone, and slid the financial charts across the high chair.",
                "act2": "'Look team, 2 PM tummy time produces negative ROI. If we swap milk bottles for cold brew and outsource diaper changes to junior analysts, our sleep-adjusted margins double.'",
                "act3": "He slammed his tiny sippy cup on the desk, stared straight into the lens, and said: 'Sign the pacifier agreement or I cry during your Zoom call with the investors.'",
                "scenes": [
                    {
                        "text": "POV: Your 10-month-old calls an emergency 6 AM boardroom meeting to renegotiate nap times.",
                        "visual_prompt": "Cinematic shot of a chubby baby in tailored navy pinstripe suit sitting at massive mahogany boardroom table with Shure SM7B studio microphone, serious executive expression, 8k, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "'Tummy time yields zero shareholder value. We need to restructure formula allocations immediately.'",
                        "visual_prompt": "Baby executive holding a tiny golden pointer toward a financial graph on a wall projector showing milk bottle vs nap projections, Wall Street aesthetic, photorealistic 8k, 9:16 vertical",
                        "motion": "pan_left"
                    },
                    {
                        "text": "He slammed his sippy cup and gave his final ultimatum before his morning teething break.",
                        "visual_prompt": "Dramatic close-up of baby boss with a fierce deadpan CEO stare, gold baby watch reflecting rim lighting, cinematic depth of field, award-winning lighting, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "satire_comedy"
            },
            {
                "title": "Baby Street Food Mogul: The Pani Puri Empire",
                "hook": "Why work corporate when you can make 5,000 dollars a day selling street momos as a toddler?",
                "act1": "At 4 PM in Old Delhi, Baby Leo tied his miniature bandana, rolled up his sleeves, and heated up the copper tawa.",
                "act2": "His tiny hands cracked spiced puris at 180 units per minute. Street vendors twice his age took notes while Leo managed UPI QR codes on his baby monitor.",
                "act3": "A customer asked for extra spicy chutney. Leo looked him up and down, shook his head, and gave him sweet tamarind: 'You can't handle the heat, my friend. Stick to cerelac.'",
                "scenes": [
                    {
                        "text": "Why work corporate when you can make five grand a day selling street food as a toddler?",
                        "visual_prompt": "Vibrant bustling night street food market in Old Delhi, a chubby cute toddler wearing a tiny chef apron standing on a wooden crate behind a glowing brass stall, cinematic street photography, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "His tiny hands cracked spiced puris with superhuman precision while lines wrapped around the corner.",
                        "visual_prompt": "Ultra-detailed shot of tiny hands splashing spiced mint water into a crispy golden pani puri with steam and droplets catching golden neon streetlights, photorealistic 8k, 9:16 vertical",
                        "motion": "pan_right"
                    },
                    {
                        "text": "He refused spicy chutney to a tourist and told him to stick to baby cereal.",
                        "visual_prompt": "Baby street food vendor giving a hilarious side-eye look to the camera while holding a stainless steel spoon, neon stall lights blurred in background, 8k award-winning photography, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "acoustic_breeze",
                "soundtrack_genre": "street_comedy"
            }
        ]
    },

    "emotional_animal_sagas": {
        "id": "emotional_animal_sagas",
        "title": "Paws of Hope (Cinematic Animal Stories)",
        "category": "emotional_animal",
        "description": "High-retention cinematic mini-films with genuine emotional arcs, struggles, and triumphant resolutions.",
        "cast": [
            {
                "id": "stray_scout",
                "name": "Scout & Little Nova",
                "species": "Golden Retriever & Calico Kitten",
                "traits": "Weathered gentle golden dog and tiny shivering calico kitten with striking amber eyes",
                "visual_token": "a gentle weathered golden retriever with kind soulful eyes protecting a tiny shivering calico kitten in a warm sheltered alcove, cinematic rain"
            }
        ],
        "default_voice": "en-US-EricNeural",
        "episodes": [
            {
                "title": "The Storm Under the Red Bridge",
                "hook": "For three days, this gentle stray dog guarded an abandoned cardboard box in torrential rain.",
                "act1": "Passersby hurried past in their raincoats, never looking down. Under the iron bridge, Scout curled his wet golden body around a soggy shoebox, refusing to leave.",
                "act2": "When a railway mechanic finally knelt down with a flashlight, Scout didn't growl. He gently nudged the lid open with his wet nose, revealing a shivering 4-week-old calico kitten.",
                "act3": "The mechanic carried them both home inside his warm jacket. Today, they sleep together by the fireplace — and Scout still checks on her every two hours.",
                "scenes": [
                    {
                        "text": "For three days, this gentle stray dog guarded an abandoned cardboard box in torrential rain.",
                        "visual_prompt": "Cinematic rainy evening under an ancient iron bridge, a large gentle golden retriever lying in the puddles shielding a small cardboard box with his body, neon street reflections, emotional lighting, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "When a mechanic approached, the dog gently nudged the lid open to reveal a tiny shivering kitten.",
                        "visual_prompt": "Warm flashlight beam cutting through the rain, revealing the gentle dog nudging a tiny wet calico kitten with huge amber eyes, emotional masterpiece photography, 8k, 9:16 vertical",
                        "motion": "parallax_dolly"
                    },
                    {
                        "text": "Today, they sleep together by the fireplace, and he still checks on her every single night.",
                        "visual_prompt": "Cozy living room hearth with crackling golden fire, the golden dog resting his chin peacefully over the sleeping kitten curled on his front paws, soft volumetric fire glow, 8k photorealistic, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "heartwarming"
            }
        ]
    },

    "fictional_pov": {
        "id": "fictional_pov",
        "title": "Through Alternate Eyes (Immersive Fictional POV)",
        "category": "fictional_pov",
        "description": "Transporting viewers into breathtaking impossible vantage points across eras and realities.",
        "cast": [],
        "default_voice": "en-US-ChristopherNeural",
        "episodes": [
            {
                "title": "POV: You Are The Last Radio Operator in 2099",
                "hook": "POV: It is midnight in 2099, and your radio antenna just picked up a broadcast from 1944.",
                "act1": "Three hundred feet above the sunken ruins of Neo-Tokyo, the aurora borealis hums across the ionosphere while your vacuum tubes crackle.",
                "act2": "Through eight decades of static, a woman's voice suddenly emerges clear as ice: 'If anyone can hear this from the future, the war ended. Tell us we survived.'",
                "act3": "You reach for your transmitter switch, hold your breath, and whisper into the cold night: 'You survived. And the stars are still here.'",
                "scenes": [
                    {
                        "text": "POV: It is midnight in 2099, and your radio antenna just picked up a broadcast from 1944.",
                        "visual_prompt": "First-person perspective looking out from a high-tech glowing radio tower cabin overlooking a cyberpunk metropolis in rain, glowing neon HUD dials and vacuum tube amplifiers, 8k cinematic, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Through eighty years of cosmic static, a voice emerges: 'Tell us we survived.'",
                        "visual_prompt": "Close-up of vintage oscilloscope displaying emerald green soundwaves flickering wildly against futuristic control panel, dramatic cinematic lighting, photorealistic 8k, 9:16 vertical",
                        "motion": "pan_left"
                    },
                    {
                        "text": "You click the brass switch and whisper: 'You survived. And the stars are still here.'",
                        "visual_prompt": "Breathtaking panoramic view from the tower window into a vast starry cosmos with glowing auroras over futuristic clouds, awe-inspiring sci-fi atmosphere, 8k, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "sci_fi_emotional"
            }
        ]
    },

    "visual_asmr_satisfaction": {
        "id": "visual_asmr_satisfaction",
        "title": "Impossible Textures (AI Kinetic ASMR)",
        "category": "asmr_satisfying",
        "description": "Hypnotic, ultra-crisp visual loops with pristine sound design and satisfying tactile physics.",
        "cast": [],
        "default_voice": "en-US-JennyNeural",
        "episodes": [
            {
                "title": "The Glass Watermelon Slice",
                "hook": "Watch what happens when a heated titanium scalpel cuts through solid ruby glass fruit.",
                "act1": "Under macro studio lighting, a translucent crystal watermelon rests on black volcanic slate, glowing with internal ruby refraction.",
                "act2": "A glowing 1,000-degree titanium blade glides down with effortless glassy precision, peeling paper-thin micro-shards that ring like crystal chimes.",
                "act3": "The slice falls in slow-motion, revealing a core of liquid golden honey that flows without a single ripple.",
                "scenes": [
                    {
                        "text": "Watch what happens when a heated titanium scalpel cuts through solid ruby glass fruit.",
                        "visual_prompt": "Macro 8k photograph of a hyper-realistic translucent watermelon made of glowing ruby crystal glass on black obsidian slate, internal caustics, Octane render quality, 9:16 vertical",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "The blade glides down, slicing micro-thin glassy ribbons that ring like crystal chimes.",
                        "visual_prompt": "Ultra-macro slow motion capture of a heated glowing titanium edge peeling a hair-thin curved shard of glowing red glass, tiny sparkling crystal dust particles, 9:16 vertical",
                        "motion": "parallax_dolly"
                    },
                    {
                        "text": "The slice reveals an impossible core of thick liquid gold honey flowing in perfect silence.",
                        "visual_prompt": "Close-up of the sliced glass fruit revealing thick golden viscous liquid oozing in hypnotic slow-motion, pristine studio lighting, photorealistic 8k, 9:16 vertical",
                        "motion": "zoom_out"
                    }
                ],
                "music": "lofi_chill",
                "soundtrack_genre": "satisfying_ambient"
            }
        ]
    }
}

# ==============================================================================
# UNIVERSE MANAGER IMPLEMENTATION
# ==============================================================================

class UniverseManager:
    """Manages persistent universe state, episodic continuity, and story generation."""

    @classmethod
    def _load_state(cls) -> Dict[str, Any]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not STATE_FILE.exists():
            default_state = {
                "active_universe": "mochi_and_friends",
                "universe_counters": {
                    "mochi_and_friends": {"season": 1, "episode": 0, "history": []},
                    "baby_boss_ventures": {"season": 1, "episode": 0, "history": []},
                    "emotional_animal_sagas": {"season": 1, "episode": 0, "history": []},
                    "fictional_pov": {"season": 1, "episode": 0, "history": []},
                    "visual_asmr_satisfaction": {"season": 1, "episode": 0, "history": []}
                }
            }
            cls._save_state(default_state)
            return default_state
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"active_universe": "mochi_and_friends", "universe_counters": {}}

    @classmethod
    def _save_state(cls, state: Dict[str, Any]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_all_universes(cls) -> Dict[str, Any]:
        """Returns metadata for all available character universes."""
        state = cls._load_state()
        result = {}
        for uid, udata in UNIVERSES.items():
            counter = state.get("universe_counters", {}).get(uid, {"season": 1, "episode": 0})
            result[uid] = {
                "id": uid,
                "title": udata["title"],
                "category": udata["category"],
                "description": udata["description"],
                "cast_count": len(udata.get("cast", [])),
                "current_season": counter.get("season", 1),
                "current_episode": counter.get("episode", 0),
                "total_episodes_available": len(udata.get("episodes", []))
            }
        return result

    @classmethod
    def get_active_universe_info(cls) -> Dict[str, Any]:
        state = cls._load_state()
        uid = state.get("active_universe", "mochi_and_friends")
        if uid not in UNIVERSES:
            uid = "mochi_and_friends"
        universe = UNIVERSES[uid]
        counter = state.get("universe_counters", {}).get(uid, {"season": 1, "episode": 0})
        return {
            "universe_id": uid,
            "title": universe["title"],
            "category": universe["category"],
            "description": universe["description"],
            "cast": universe.get("cast", []),
            "current_season": counter.get("season", 1),
            "current_episode": counter.get("episode", 0)
        }

    @classmethod
    def set_active_universe(cls, universe_id: str) -> bool:
        if universe_id not in UNIVERSES:
            return False
        state = cls._load_state()
        state["active_universe"] = universe_id
        cls._save_state(state)
        return True

    @classmethod
    def generate_next_episode(
        cls,
        universe_id: Optional[str] = None,
        custom_premise: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes the next canonical episode in the universe with strict 3-act viral architecture.
        Increments the episode counter and stores historical continuity.
        """
        state = cls._load_state()
        uid = universe_id or state.get("active_universe", "mochi_and_friends")
        if uid not in UNIVERSES:
            uid = "mochi_and_friends"

        universe = UNIVERSES[uid]
        counters = state.setdefault("universe_counters", {})
        u_counter = counters.setdefault(uid, {"season": 1, "episode": 0, "history": []})

        current_ep = u_counter.get("episode", 0) + 1
        season = u_counter.get("season", 1)
        if current_ep > 25:
            season += 1
            current_ep = 1

        u_counter["episode"] = current_ep
        u_counter["season"] = season

        available_episodes = universe.get("episodes", [])
        ep_index = (current_ep - 1) % len(available_episodes) if available_episodes else 0
        blueprint = available_episodes[ep_index] if available_episodes else {}

        # Episode Title & Story Arc
        ep_code = f"S{season:02d}E{current_ep:02d}"
        full_title = f"{universe['title'].split('(')[0].strip()}: {blueprint.get('title', 'A New Adventure')} ({ep_code})"

        # 3-Act Script Construction
        hook = blueprint.get("hook", f"Episode {current_ep}: The story unfolds.")
        act1 = blueprint.get("act1", "")
        act2 = blueprint.get("act2", "")
        act3 = blueprint.get("act3", "")
        full_script = f"{hook} {act1} {act2} {act3}".strip()

        scenes = blueprint.get("scenes", [])
        voice = universe.get("default_voice", "en-US-ChristopherNeural")
        music = blueprint.get("music", "lofi_chill")

        # Record history
        u_counter.setdefault("history", []).append({
            "code": ep_code,
            "title": full_title,
            "category": universe["category"]
        })
        # Keep last 50
        u_counter["history"] = u_counter["history"][-50:]
        cls._save_state(state)

        return {
            "id": f"{uid}_{ep_code.lower()}_{random.randint(1000, 9999)}",
            "universe_id": uid,
            "season": season,
            "episode": current_ep,
            "episode_code": ep_code,
            "title": full_title,
            "genre": universe["category"],
            "hook": hook,
            "script": full_script,
            "scenes": scenes,
            "suggested_voice": voice,
            "suggested_music": music,
            "cast": universe.get("cast", []),
            "visual_style": "photorealistic",
            "narrative_structure": {
                "act1_hook": act1,
                "act2_escalation": act2,
                "act3_payoff": act3
            }
        }
