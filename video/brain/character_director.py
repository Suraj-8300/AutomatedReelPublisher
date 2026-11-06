"""
Character Director for AutoReelStudio.
Provides persistent character profiles, distinctive markings, accessories, and duo dynamics
for cute animals and narrative storytelling reels.
"""

import random
from typing import Dict, Any, List, Optional

ANIMAL_SPECIES = [
    {"species": "kitten", "label": "Ginger Scottish Fold Kitten", "default_name": "Mochi", "size": "tiny"},
    {"species": "puppy", "label": "Golden Retriever Puppy", "default_name": "Barnaby", "size": "small"},
    {"species": "rabbit", "label": "Holland Lop Bunny", "default_name": "Pip", "size": "tiny"},
    {"species": "panda", "label": "Fluffy Baby Giant Panda", "default_name": "Bao Bao", "size": "chubby"},
    {"species": "red_panda", "label": "Curious Red Panda", "default_name": "Rusty", "size": "small"},
    {"species": "hamster", "label": "Chubby Golden Hamster", "default_name": "Peanut", "size": "tiny"},
    {"species": "capybara", "label": "Gentle Chill Capybara", "default_name": "Gus", "size": "medium"},
    {"species": "duckling", "label": "Fuzzy Yellow Duckling", "default_name": "Pebble", "size": "tiny"},
    {"species": "penguin", "label": "Baby Emperor Penguin Chick", "default_name": "Pippin", "size": "small"},
    {"species": "fox", "label": "Clever Little Red Fox Cub", "default_name": "Felix", "size": "small"},
    {"species": "deer", "label": "Spotted Woodland Fawn", "default_name": "Willow", "size": "medium"},
    {"species": "otter", "label": "Playful River Otter Pup", "default_name": "Splashes", "size": "small"},
    {"species": "owl", "label": "Round Saw-Whet Owlet", "default_name": "Hootie", "size": "tiny"},
    {"species": "chick", "label": "Fuzzy Little Yellow Baby Chick", "default_name": "Sunny", "size": "tiny"}
]

UNUSUAL_DUOS = [
    {
        "duo_name": "The Baker & The Little Helper",
        "char1": {"species": "kitten", "name": "Mochi", "breed": "Orange Tabby Kitten", "role": "Master Baker"},
        "char2": {"species": "duckling", "name": "Pebbles", "breed": "Fuzzy Yellow Duckling", "role": "Quality Tester"}
    },
    {
        "duo_name": "The Gentle Giant & The Tiny Scout",
        "char1": {"species": "capybara", "name": "Gus", "breed": "Zen Capybara", "role": "Calm Mentor"},
        "char2": {"species": "chick", "name": "Pip", "breed": "Baby Yellow Chick", "role": "Excited Navigator"}
    },
    {
        "duo_name": "The Detective & The Apprentice",
        "char1": {"species": "puppy", "name": "Sherlock Paws", "breed": "Beagle Puppy", "role": "Lead Detective"},
        "char2": {"species": "rabbit", "name": "Clover", "breed": "Lop Bunny", "role": "Clue Finder"}
    },
    {
        "duo_name": "The Forest Explorers",
        "char1": {"species": "fox", "name": "Rusty", "breed": "Red Fox Cub", "role": "Pathfinder"},
        "char2": {"species": "owl", "name": "Hootie", "breed": "Baby Owlet", "role": "Night Lookout"}
    },
    {
        "duo_name": "The River Guardians",
        "char1": {"species": "otter", "name": "Barnacle", "breed": "Playful River Otter", "role": "Swimmer"},
        "char2": {"species": "kitten", "name": "Biscuit", "breed": "Adventurous Calico Kitten", "role": "Lookout"}
    }
]

ACCESSORIES = [
    "tiny white chef hat and red neckerchief",
    "miniature yellow raincoat and tiny rubber boots",
    "cozy hand-knitted emerald green wool scarf",
    "round vintage wire-rimmed glasses and bow tie",
    "miniature leather aviator goggles pushed up on forehead",
    "tiny teal denim overalls with front pouch",
    "miniature leather messenger bag slung across chest",
    "red polka-dot baker apron tied neatly around waist",
    "tiny golden detective magnifying glass on a ribbon",
    "miniature red plaid bandana tied loosely at collar"
]

DISTINCTIVE_MARKINGS = [
    "distinct white paws resembling little socks and a pink heart-shaped nose",
    "one floppy left ear and a gentle white patch over the right eye",
    "extra fluffy ear tufts and wide expressive amber eyes",
    "silky creamy underbelly and adorable freckles across the muzzle",
    "distinctive white lightning-streak marking on the chest",
    "round button eyes and a cute tip of white fur on the tail"
]


class CharacterDirector:
    """Manages visual identity, character consistency tokens, and duo dynamics."""

    @staticmethod
    def create_character_profile(
        species: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        rng = random.Random(seed) if seed is not None else random.Random()

        if species:
            match = next((s for s in ANIMAL_SPECIES if s["species"] == species.lower()), None)
            spec_data = match if match else rng.choice(ANIMAL_SPECIES)
        else:
            spec_data = rng.choice(ANIMAL_SPECIES)

        markings = rng.choice(DISTINCTIVE_MARKINGS)
        accessory = rng.choice(ACCESSORIES)

        return {
            "name": spec_data["default_name"],
            "species": spec_data["species"],
            "label": spec_data["label"],
            "size": spec_data["size"],
            "markings": markings,
            "accessory": accessory,
            "signature": f"{spec_data['label']} named {spec_data['default_name']}, {markings}, wearing {accessory}"
        }

    @staticmethod
    def create_duo_profile(seed: Optional[int] = None) -> Dict[str, Any]:
        rng = random.Random(seed) if seed is not None else random.Random()
        duo_template = rng.choice(UNUSUAL_DUOS)
        c1 = duo_template["char1"]
        c2 = duo_template["char2"]

        acc1 = rng.choice(ACCESSORIES)
        acc2 = rng.choice(ACCESSORIES)
        while acc2 == acc1:
            acc2 = rng.choice(ACCESSORIES)

        return {
            "is_duo": True,
            "duo_title": duo_template["duo_name"],
            "character_1": {
                "name": c1["name"],
                "species": c1["species"],
                "breed": c1["breed"],
                "role": c1["role"],
                "accessory": acc1,
            },
            "character_2": {
                "name": c2["name"],
                "species": c2["species"],
                "breed": c2["breed"],
                "role": c2["role"],
                "accessory": acc2,
            }
        }
