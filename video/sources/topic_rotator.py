"""
Daily topic seed rotator for AutoReelStudio.
Provides curated topic seeds for each pillar so the pipeline always has content
even when Wikipedia feeds are unavailable.
"""

import random
from typing import List, Tuple

# (topic, pillar) seed pools
_CINEMATIC_SEEDS = [
    "A neutron star collision generating gravitational waves",
    "The last moment before a black hole's event horizon",
    "A quantum computer solving an unsolvable equation",
    "The birth of the first star in the universe",
    "An antimatter reaction photographed for the first time",
    "The moment a wormhole stabilizes in deep space",
    "Light bending around a supermassive black hole",
    "The final pulse of a dying magnetar",
    "Dark matter visualized for the first time",
    "A plasma storm on the surface of the sun",
    "The edge of the observable universe",
    "A rogue planet moving silently through the cosmos",
]

_SCIENCE_SEEDS = [
    "CRISPR gene editing just cured a genetic disease",
    "Scientists discovered a new state of matter",
    "A new antibiotic that defeats drug-resistant bacteria",
    "The largest structure in the universe discovered",
    "Quantum entanglement used for real communication",
    "A room-temperature superconductor verified",
    "New evidence of water on Mars subsurface",
    "AI predicts protein structures faster than ever",
    "Telescope captures image of an exoplanet atmosphere",
    "First lab-grown human organ successfully transplanted",
    "Ocean bacteria that eats plastic discovered",
    "The Fermi Paradox: why we haven't found aliens",
    "How the brain stores memories at the molecular level",
    "Scientists reverse aging in mice using gene therapy",
]

_MECHANICAL_SEEDS = [
    "How a jet engine generates 100,000 pounds of thrust",
    "How a nuclear reactor controls fission chain reactions",
    "How a turbocharger spins faster than the speed of sound",
    "How a gyroscope keeps spacecraft perfectly oriented",
    "How a diesel engine ignites without a spark plug",
    "How a hydraulic press generates 10,000 PSI",
    "How rocket engines gimbal to steer in space",
    "How a differential gear splits torque between wheels",
    "How a solenoid valve controls fluid flow electronically",
    "How a gas turbine converts heat into electricity",
    "How a submarine changes depth using ballast tanks",
    "How a centrifuge separates blood at 10,000 RPM",
]

_EXPLAINER_SEEDS = [
    "Why the sky is blue — Rayleigh scattering explained",
    "How Fourier Transforms see hidden frequencies in signals",
    "Why relativity says time passes slower at high speeds",
    "How RSA encryption protects every internet transaction",
    "Why entropy always increases — the second law of thermodynamics",
    "How neural networks learn patterns from data",
    "The double slit experiment that broke classical physics",
    "How GPS satellites triangulate your exact position",
    "Why quantum computers are exponentially faster",
    "How JPEG compression removes invisible information",
    "Why prime numbers are the foundation of all cryptography",
    "How DNA stores 1 exabyte of data per gram",
    "How a vaccine trains your immune system",
    "The math behind how WiFi carries data through air",
]

_ANIMAL_STORY_SEEDS = [
    "A freezing orange kitten trapped under a park bench rescued by a gentle baker",
    "A lonely golden retriever pup learning to trust human hands after rescue",
    "A tiny baby owl who fell from a nest nursed back to health by a firefighter",
    "An abandoned little duckling who adopted a giant fluffy Newfoundland dog as mom",
    "A shivering street kitten found in the snow who became a cozy bookstore guardian",
    "A frightened shelter puppy chosen by a little boy who saw his gentle spirit",
    "A lost fawn separated from its herd guided safely to the meadow by a rescue volunteer",
    "A three-legged rescue dog who protects and cuddles newborn foster kittens",
    "A hungry feral kitten rescued from an engine bay who became a boat captain's best friend",
    "A street dog who brought a tiny shivering kitten to a veterinary clinic doorstep",
    "A blind senior dog discovering the feeling of fresh soft grass for the first time",
    "A tiny orphaned red panda cub learning to climb with a plush stuffed animal",
    "A baby sea otter rescued from stormy waves learning to wrap in kelp to sleep",
    "A loyal street dog who waited outside a bakery every sunrise until adopted",
]

PILLAR_SEEDS = {
    "animal_story": _ANIMAL_STORY_SEEDS,
    "storytelling": _ANIMAL_STORY_SEEDS,
    "cinematic":    _CINEMATIC_SEEDS,
    "science":      _SCIENCE_SEEDS,
    "mechanical":   _MECHANICAL_SEEDS,
    "explainer":    _EXPLAINER_SEEDS,
}

ALL_PILLARS = list(PILLAR_SEEDS.keys())

# Daily schedule pattern for 10-reel batch (prioritizes viral animal stories & high-retention genres)
DAILY_SCHEDULE = [
    "animal_story", "science", "animal_story", "mechanical",
    "storytelling", "explainer", "animal_story", "cinematic",
    "storytelling", "science",
]


class TopicRotator:
    """Provides curated topic seeds for each content pillar."""

    @staticmethod
    def get_topic(pillar: str) -> str:
        """Returns a random curated topic for the given pillar."""
        seeds = PILLAR_SEEDS.get(pillar, _ANIMAL_STORY_SEEDS)
        return random.choice(seeds)

    @staticmethod
    def get_daily_schedule(count: int = 10) -> List[Tuple[str, str]]:
        """
        Returns a list of (pillar, topic) tuples for a full day's batch.
        Mixes all pillars according to the daily schedule pattern.
        """
        schedule = []
        for i in range(count):
            pillar = DAILY_SCHEDULE[i % len(DAILY_SCHEDULE)]
            topic = TopicRotator.get_topic(pillar)
            schedule.append((pillar, topic))
        return schedule

    @staticmethod
    def detect_pillar(topic: str) -> str:
        """
        Heuristically detects the best pillar for a given topic string.
        Used when the user provides a custom topic without specifying a pillar.
        """
        t = topic.lower()
        animal_kw = ["kitten", "puppy", "cat", "dog", "animal", "rescue", "rescued",
                     "duckling", "owl", "fawn", "otter", "panda", "pet", "shelter",
                     "baker", "furry", "paw", "purr", "bark", "tail", "cute",
                     "heartwarming", "biscuit", "friendship", "adoption", "adopted"]
        story_kw = ["story of", "tale of", "journey", "the little", "who saved",
                    "who found", "never gave up", "miracle", "once upon"]
        mechanical_kw = ["engine", "motor", "gear", "pump", "turbine", "reactor",
                         "piston", "valve", "compressor", "submarine", "hydraulic",
                         "mechanism", "machine", "works", "how does"]
        explainer_kw = ["math", "equation", "theorem", "algorithm", "formula",
                        "explained", "why", "encryption", "fourier", "quantum bit",
                        "neural network", "dna", "compression", "cryptography"]
        science_kw = ["discovery", "scientist", "research", "gene", "crispr", "telescope",
                      "breakthrough", "study", "new evidence", "first time", "organism",
                      "particle", "experiment", "vaccine", "climate"]
        cinematic_kw = ["black hole", "neutron star", "universe", "cosmos", "dark matter",
                        "antimatter", "wormhole", "plasma", "supernova", "event horizon"]

        for kw in animal_kw:
            if kw in t:
                return "animal_story"
        for kw in story_kw:
            if kw in t:
                return "animal_story"
        for kw in mechanical_kw:
            if kw in t:
                return "mechanical"
        for kw in explainer_kw:
            if kw in t:
                return "explainer"
        for kw in cinematic_kw:
            if kw in t:
                return "cinematic"
        for kw in science_kw:
            if kw in t:
                return "science"
        return "animal_story"  # Default fallback is heartwarming story
