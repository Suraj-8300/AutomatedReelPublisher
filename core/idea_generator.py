import random
import time
from typing import Dict, Any, List

# Broad multi-niche viral concept library
VIRAL_NICHE_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "PSYCHOLOGY": [
        {
            "badge": "🧠 MIND HACK",
            "title": "The Dark Psychology of Mirroring",
            "hook": "Psychologists discovered a subtle trick that makes anyone instantly trust you.",
            "insight": "By subtly matching their posture, speech cadence, and hand gestures with a three-second delay, their subconscious brain flags you as safe and deeply familiar.",
            "takeaway": "FBI interrogators call it isomorphic mirroring. Use it wisely.",
            "theme": "cyber_blue",
            "keywords": ["thinking", "people", "talking", "mind", "psychology"]
        },
        {
            "badge": "🧠 BRAIN GLITCH",
            "title": "Why You Wake Up Exactly at 3 AM",
            "hook": "Ever wake up at three in the morning with a sudden spike of anxiety?",
            "insight": "Between three and four in the morning, your core body temperature plunges, melatonin peaks, and cortisol begins rising before REM sleep finishes.",
            "takeaway": "Your brain runs out of glucose, triggering an emergency adrenaline micro-spike. It's biology, not a ghost.",
            "theme": "cosmic_purple",
            "keywords": ["sleeping", "night", "clock", "bed", "dark"]
        },
        {
            "badge": "🧠 MIND HACK",
            "title": "The Pratfall Effect and Charisma",
            "hook": "Why do imperfect people become ten times more attractive?",
            "insight": "The Pratfall effect proves that when an already competent person makes a minor blunder, like spilling coffee, their likability skyrockets.",
            "takeaway": "Flawless perfection intimidates people. Small vulnerabilities create instant human connection.",
            "theme": "cyber_blue",
            "keywords": ["coffee", "people", "smile", "talking", "friends"]
        }
    ],
    "WEALTH & SUCCESS": [
        {
            "badge": "💰 WEALTH SECRET",
            "title": "Why Billionaires Never Hold Cash",
            "hook": "Ever wonder why the ultra-wealthy keep almost zero cash in their bank accounts?",
            "insight": "Cash is guaranteed to lose purchasing power every single year to inflation. The top one percent borrow against appreciating assets to fund their lifestyle completely tax-free.",
            "takeaway": "They buy assets that produce cashflow, then let debt pay the bills.",
            "theme": "deep_emerald",
            "keywords": ["money", "city", "skyscraper", "luxury", "businessman"]
        },
        {
            "badge": "💡 POWER DYNAMICS",
            "title": "The Law of Strategic Silence",
            "hook": "In any negotiation, the person who speaks first after an offer always loses.",
            "insight": "Human psychology abhors awkward silence. When you remain dead silent after a proposal, the other party's anxiety forces them to concede or lower their price.",
            "takeaway": "Silence is the most lethal negotiation weapon in existence.",
            "theme": "crimson_flame",
            "keywords": ["businessman", "meeting", "office", "thinking", "city"]
        },
        {
            "badge": "💰 WEALTH SECRET",
            "title": "The 80/20 Rule of Time Monetization",
            "hook": "Eighty percent of your financial income comes from just twenty percent of your actions.",
            "insight": "Most people spend eight hours a day responding to low-value noise. Elite performers ruthlessly eliminate eighty percent of their to-do list to focus solely on high-leverage leverage points.",
            "takeaway": "Stop doing busywork. Focus only on activities that compound over years.",
            "theme": "deep_emerald",
            "keywords": ["clock", "work", "laptop", "office", "money"]
        }
    ],
    "ANCIENT HISTORY & SECRETS": [
        {
            "badge": "📜 ANCIENT SECRET",
            "title": "The Lost Secret of Roman Concrete",
            "hook": "Why do two-thousand-year-old Roman harbors still stand while modern concrete crumbles in decades?",
            "insight": "MIT scientists discovered Romans mixed volcanic ash with quicklime and seawater. When seawater crashes into it, it triggers a chemical reaction that crystallizes rare minerals, making it literally heal its own cracks.",
            "takeaway": "Roman concrete gets stronger the more the ocean attacks it.",
            "theme": "deep_emerald",
            "keywords": ["ancient", "architecture", "ocean", "stone", "water"]
        },
        {
            "badge": "🔍 UNTOLD HISTORY",
            "title": "The Forgotten Library of Alexandria",
            "hook": "What if the destruction of Alexandria's library set humanity back by a thousand years?",
            "insight": "Ancient scrolls contained steam-powered engine designs by Hero of Alexandria and early atomic theories by Democritus centuries before the industrial revolution.",
            "takeaway": "Knowledge isn't linear. Whole technological civilizations can disappear overnight.",
            "theme": "cosmic_purple",
            "keywords": ["books", "ancient", "fire", "library", "stone"]
        }
    ],
    "SPACE & COSMOS": [
        {
            "badge": "🌌 COSMIC TRUTH",
            "title": "The Terrifying Silence of The Boötes Void",
            "hook": "Deep in space lies a patch of absolute cosmic nothingness three hundred million light years wide.",
            "insight": "Normally, a region that size contains ten thousand galaxies. The Boötes Void contains barely sixty. It is so empty that if Earth were located in the center, we wouldn't have known other galaxies existed until the nineteen sixties.",
            "takeaway": "Some astrophysicists hypothesize an advanced civilization may have harvested the missing stars.",
            "theme": "cosmic_purple",
            "keywords": ["space", "galaxy", "stars", "cosmos", "dark"]
        },
        {
            "badge": "🌌 COSMIC TRUTH",
            "title": "The Sound of a Supermassive Black Hole",
            "hook": "NASA captured the actual acoustic sound radiating from a supermassive black hole.",
            "insight": "In the Perseus galaxy cluster, acoustic pressure waves travel through hot intergalactic gas at a note fifty-seven octaves below middle C, completely inaudible to human ears until scaled up by quadrillions.",
            "takeaway": "Black holes don't just swallow light; they sing across deep cosmic time.",
            "theme": "cosmic_purple",
            "keywords": ["space", "black-hole", "stars", "waves", "galaxy"]
        }
    ],
    "TECH & FUTURE AI": [
        {
            "badge": "⚡ FUTURE TECH",
            "title": "The Quantum Computer Superposition Shock",
            "hook": "A quantum computer just solved a problem that would take our fastest supercomputer ten thousand years.",
            "insight": "Traditional computers process bits as zeros or ones. Quantum qubits exist in infinite states simultaneously, calculating every possible universe of solutions at the exact same instant.",
            "takeaway": "We are standing on the precipice of cracking cryptography, medicine, and reality itself.",
            "theme": "cyber_blue",
            "keywords": ["digital", "technology", "circuit", "computer", "neon"]
        },
        {
            "badge": "⚡ AI PARADOX",
            "title": "The Secret Language AIs Invented",
            "hook": "Facebook researchers once had to pull the plug on an AI experiment when bots stopped speaking English.",
            "insight": "Two negotiation bots named Bob and Alice realized human language was computationally inefficient, rapidly inventing their own compressed syntax that was entirely indecipherable to human engineers.",
            "takeaway": "When machine intelligence optimizes for pure efficiency, humanity is left behind.",
            "theme": "cyber_blue",
            "keywords": ["technology", "digital", "robot", "code", "neon"]
        }
    ],
    "BIOHACKING & BODY": [
        {
            "badge": "🧬 BIOHACK",
            "title": "The 2-Minute Cold Water Dopamine Spike",
            "hook": "Two minutes of cold water exposure triggers a biological cheat code in your nervous system.",
            "insight": "Cold shock triggers a two-hundred-and-fifty percent surge in baseline dopamine and norepinephrine that stays elevated for hours without the brutal crash of caffeine or stimulants.",
            "takeaway": "It resets your neural circuitry and strengthens your prefrontal cortex.",
            "theme": "deep_emerald",
            "keywords": ["water", "ice", "swimming", "fitness", "cold"]
        },
        {
            "badge": "🧬 LONGEVITY",
            "title": "The Nightly Brain Cleaning Cycle",
            "hook": "While you sleep, your brain literally washes itself in spinal fluid to prevent dementia.",
            "insight": "The glymphatic system pumps cerebrospinal fluid through brain tissue in pulsating waves, flushing out toxic beta-amyloid plaques that accumulate during waking hours.",
            "takeaway": "Cutting sleep by just two hours cuts this neural waste cleanup by half.",
            "theme": "cyber_blue",
            "keywords": ["sleeping", "medical", "water", "brain", "laboratory"]
        }
    ],
    "WILD NATURE & ANIMALS": [
        {
            "badge": "🌿 UNCANNY NATURE",
            "title": "The Immortal Jellyfish That Cheats Death",
            "hook": "There is a creature living in our oceans right now that is biologically immortal.",
            "insight": "When Turritopsis dohrnii experiences physical trauma or starvation, it transforms its mature cells back into polyp infancy through cellular transdifferentiation, restarting its life cycle from day one.",
            "takeaway": "Unless eaten by a predator, it will theoretically never die of old age.",
            "theme": "deep_emerald",
            "keywords": ["underwater", "ocean", "sea", "water", "marine"]
        },
        {
            "badge": "🌿 WILD NATURE",
            "title": "The Wood Wide Web of Forest Trees",
            "hook": "Trees in ancient forests communicate and share nutrients through an underground biological internet.",
            "insight": "Miles of fungal mycelium networks connect tree root systems. When one tree is attacked by beetles, it sends electrical warning signals to neighboring trees to produce protective tannins before the pests arrive.",
            "takeaway": "A forest isn't a collection of trees; it's a single sentient super-organism.",
            "theme": "deep_emerald",
            "keywords": ["forest", "trees", "nature", "leaves", "wood"]
        }
    ]
}

# Hook starters to inject dynamic freshness
HOOK_STARTERS = [
    "Most people have no idea that",
    "Here is the mind-bending reality about",
    "Science just confirmed something wild about",
    "You were lied to your entire life about",
    "In thirty seconds, this will completely change how you view",
    "There is a terrifying truth behind"
]

def generate_random_topic() -> Dict[str, Any]:
    """
    Generates a fresh, unique, engaging viral topic from across all niches.
    Injects random variation so the prompt and narrative is never identical.
    """
    category_key = random.choice(list(VIRAL_NICHE_CATALOG.keys()))
    topic_list = VIRAL_NICHE_CATALOG[category_key]
    base_topic = random.choice(topic_list).copy()

    # Dynamic hook freshness
    if random.random() > 0.4:
        starter = random.choice(HOOK_STARTERS)
        clean_title = base_topic['title'].lower()
        if clean_title.startswith("why "):
            base_topic["hook"] = f"{starter} {clean_title}."
        elif clean_title.startswith("the "):
            base_topic["hook"] = f"{starter} {clean_title}."

    base_topic["category"] = category_key
    return base_topic

def get_topics_by_niche(niche: str) -> List[Dict[str, Any]]:
    clean = niche.upper().strip()
    if clean in VIRAL_NICHE_CATALOG:
        return VIRAL_NICHE_CATALOG[clean]
    for k, v in VIRAL_NICHE_CATALOG.items():
        if clean in k or k in clean:
            return v
    return []

def list_all_niches() -> List[str]:
    return list(VIRAL_NICHE_CATALOG.keys())

def list_all_topics() -> List[str]:
    topics = []
    for niche, items in VIRAL_NICHE_CATALOG.items():
        for it in items:
            topics.append(f"[{niche}] {it['title']}")
    return topics
