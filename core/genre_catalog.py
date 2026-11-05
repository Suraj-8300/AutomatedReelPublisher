import random
from typing import Dict, Any, List, Optional

# Rich catalog across all 9 genres with verified facts, real comedic setups, and cinematic narratives
GENRE_TOPICS_DATABASE: Dict[str, List[Dict[str, Any]]] = {
    "comedy": [
        {
            "subgenre": "relatable_everyday",
            "title": "The Grocery Store Cart Trajectory Law",
            "hook": "Why does every single shopping cart choose violence the moment you enter the aisle?",
            "script_15s": "Shopping carts have four wheels, but three of them are actively plotting against the fourth. You try steering toward the bread, and suddenly you are drifting Tokyo-style into organic cereal. It is physics, but malicious.",
            "script_30s": "Every grocery cart on Earth has one wheel that works for the government, two that are on strike, and one that vibrates at the resonant frequency of pure chaos. You walk in calmly planning to buy milk. Five seconds later, you are locked in an arm-wrestling contest with a metal basket drifting into an innocent pyramid of pasta sauce. The worst part? You pretend you did it on purpose.",
            "keywords": ["supermarket", "shopping", "funny", "people", "store"],
            "badge": "😂 EVERY TIME",
            "theme": "crimson_flame",
            "source": "Observational Human Experience"
        },
        {
            "subgenre": "unexpected_punchline",
            "title": "Why Coffee Makes You Think You Can Conquer The World",
            "hook": "Ever notice that coffee gives you thirty minutes of pure genius followed by existential dread?",
            "script_15s": "First sip: I am drafting three business plans and fixing my entire life by noon. Sixty minutes later: Staring blankly at a wall, wondering if pigeons ever get tired of flying. Caffeine does not give energy; it borrows tomorrow's energy with twenty percent interest.",
            "script_30s": "At 8 AM, after one iced espresso, you feel like an unstoppable entrepreneur about to disrupt three separate industries before lunch. You organize your desktop, you respond to emails with aggressive optimism. Then at 11 AM, the crash arrives. Suddenly you are paralyzed on the couch debating whether your ceiling fan is judging your life choices. Caffeine is just a high-interest loan on tomorrow's sanity.",
            "keywords": ["coffee", "cup", "morning", "funny", "work"],
            "badge": "☕ CAFFEINE REALITY",
            "theme": "crimson_flame",
            "source": "Humorous Daily Biology"
        },
        {
            "subgenre": "situational_comedy",
            "title": "The Wi-Fi Router's Emotional Breakdown",
            "hook": "Your Wi-Fi router works flawlessly until you have the single most important video call of your life.",
            "script_15s": "Streaming four simultaneous 4K movies? Smooth as butter. Opening your screen to give a final project presentation? Suddenly your router acts like it is transmitting signals through two wet socks across a mountain range.",
            "script_30s": "Your home Wi-Fi router has a sixth sense for panic. It happily powers twelve smart lightbulbs, your refrigerator, and a cat camera all weekend without flinching. But the second your boss asks, 'Can everyone hear me clearly?', your router enters a state of deep spiritual meditation, buffering your video into three blurry Minecraft pixels.",
            "keywords": ["computer", "wifi", "laptop", "office", "funny"],
            "badge": "📶 TECH PAIN",
            "theme": "cyber_blue",
            "source": "Modern Life Comedy"
        }
    ],
    "meme": [
        {
            "subgenre": "tech_and_code",
            "title": "Fixing One Bug in Legacy Code",
            "hook": "POV: You delete one harmless line of unused code in an old project.",
            "script_15s": "It looked like a useless comment. You delete it. Instantly, the database locks up, the server catches fire, and the company printer starts producing pictures of Nicolas Cage. Do not touch the sacred spaghetti.",
            "script_30s": "You open a repository written six years ago by an engineer who now lives in a forest with no internet. You spot one unused variable named temp_two. You delete it. Five seconds later, the authentication system collapses, the automated tests begin screaming in binary, and your Slack starts vibrating like an earthquake. You gently put the variable back. Everything works. You walk away slowly.",
            "keywords": ["code", "developer", "technology", "computer", "neon"],
            "badge": "💀 DEV PAIN",
            "theme": "cyber_blue",
            "source": "Software Engineering Culture"
        },
        {
            "subgenre": "pov_memes",
            "title": "Calculating How Much Sleep You Will Get",
            "hook": "POV: It is 2:47 AM and you are doing advanced sleep calculus.",
            "script_15s": "If I fall asleep in four minutes, I get four hours and nine minutes of sleep. If I close my eyes right now, maybe three hours and fifty-eight minutes. Your brain will literally do calculus at 3 AM to avoid actually sleeping.",
            "script_30s": "You look at your phone. 2:47 AM. Your brain immediately activates NASA-level orbital mathematics. 'Okay, if I pass out at exactly 2:53, minus seven minutes for REM cycle onset, I will wake up refreshed at 6:30.' Then you blink, and it is 3:45 AM. Now you are bargaining with the universe for an hour and twenty minutes of emergency unconsciousness.",
            "keywords": ["sleeping", "bed", "night", "clock", "dark"],
            "badge": "⏰ SLEEP MATH",
            "theme": "cosmic_purple",
            "source": "Universal Night Owl Experience"
        },
        {
            "subgenre": "workplace_humor",
            "title": "That Meeting That Could Have Been An Email",
            "hook": "POV: You just survived a forty-five minute meeting that could have been one sentence.",
            "script_15s": "Twelve people gathered in an air-conditioned room to nod thoughtfully while someone reads twenty bullet points off a slide. We traded forty-five minutes of human life for information that fit in a single tweet.",
            "script_30s": "Nothing unites human beings faster than twelve coworkers exchanging silent eye contact during a forty-five minute status update. Someone says, 'Let's take this offline and circle back.' Everyone nods like they are negotiating world peace. Meanwhile, the entire meeting could have been replaced by a nine-word Slack message: 'The document is updated, check the shared folder.'",
            "keywords": ["meeting", "office", "business", "work", "people"],
            "badge": "💼 CORPORATE REALITY",
            "theme": "deep_emerald",
            "source": "Modern Workplace Observations"
        }
    ],
    "science": [
        {
            "subgenre": "space_and_astronomy",
            "title": "The Cosmic Graveyard of Rogue Planets",
            "hook": "There are billions of dark, frozen worlds drifting through space without a star.",
            "script_15s": "Astrophysicists estimate that our Milky Way contains more rogue planets than actual stars. Ejected from their solar systems billions of years ago, these ghost worlds wander total darkness. Yet deep underground, geothermal vents could keep oceans warm enough for extraterrestrial life.",
            "script_30s": "When we look at the night sky, we picture planets peacefully orbiting suns. But astrophysicists now know space is filled with billions of rogue planets: worlds violently kicked out of their birthplace by gravitational chaos. They drift through interstellar voids in permanent sub-zero darkness. Yet beneath miles of frozen surface ice, radioactive core decay keeps hidden oceans liquid. Entire alien ecosystems could exist right now in the pitch black of deep space.",
            "keywords": ["space", "planet", "galaxy", "stars", "cosmos"],
            "badge": "🌌 NASA ASTROPHYSICS",
            "theme": "cosmic_purple",
            "source": "NASA Jet Propulsion Laboratory & Nature Astronomy"
        },
        {
            "subgenre": "quantum_physics",
            "title": "The Quantum Eraser That Rewrites the Past",
            "hook": "In quantum mechanics, a measurement made right now can change what happened in the past.",
            "script_15s": "In the delayed-choice quantum eraser experiment, physicists shot photons through slits, then chose whether to measure their paths AFTER they had already passed through. The photons retroactively altered their behavior. At the quantum level, the boundary between past and future completely dissolves.",
            "script_30s": "In 1999, physicists conducted the delayed-choice quantum eraser experiment, and what they found shook modern physics to its core. When photons pass through two slits, they form an interference pattern like waves. But if you observe which slit they take, they act like particles. The shocker? When scientists delayed the measurement until AFTER the photons hit the slits, the photons still changed their history. The present decision literally determined their past behavior.",
            "keywords": ["quantum", "physics", "technology", "abstract", "laser"],
            "badge": "🔬 QUANTUM REALITY",
            "theme": "cyber_blue",
            "source": "Physical Review Letters (Kim et al., 1999)"
        },
        {
            "subgenre": "human_biology",
            "title": "The Second Brain Inside Your Gut",
            "hook": "Your stomach produces more serotonin than your actual brain.",
            "script_15s": "The enteric nervous system lines your digestive tract with five hundred million neurons. Over ninety percent of your body's serotonin, the chemical that dictates your mood, is produced in your gut. Your intuition is not a metaphor; it is your second brain speaking directly to your thoughts.",
            "script_30s": "Ever wonder why you feel anxious in your stomach before a big speech? Your gut is lined with more than five hundred million neurons, connected directly to your brain via the vagus nerve. Medical researchers call it the enteric nervous system. It synthesizes over ninety percent of your body's serotonin and fifty percent of its dopamine. When your microbiome is out of balance, your emotional resilience drops. Taking care of your gut literally safeguards your mind.",
            "keywords": ["medical", "biology", "brain", "health", "science"],
            "badge": "🧬 HARVARD MEDICINE",
            "theme": "deep_emerald",
            "source": "Harvard Medical School Gut-Brain Axis Studies"
        }
    ],
    "mysteries": [
        {
            "subgenre": "ocean_abyss",
            "title": "The Acoustic Mystery of The Bloop",
            "hook": "In 1997, deep-sea hydrophones recorded an ultra-low frequency sound heard three thousand miles away.",
            "script_15s": "Underwater sensors in the South Pacific picked up an incomprehensibly powerful acoustic frequency. It was louder than any known blue whale and traveled across thousands of miles of open ocean. For fifteen years, marine biologists wondered what colossal entity could generate that much energy.",
            "script_30s": "During the Cold War, the US Navy built deep-sea hydrophone arrays across the Pacific to track submarines. In 1997, those sensors detected a sound so immense it registered over three thousand miles away. Named 'The Bloop', it matched the acoustic profile of an organic creature, but several times larger than the biggest whale on Earth. It took NOAA scientists until 2012 to discover the real culprit: a massive icequake tearing through Antarctic ice shelves.",
            "keywords": ["ocean", "underwater", "water", "sea", "waves"],
            "badge": "🌊 NOAA DISCOVERY",
            "theme": "cosmic_purple",
            "source": "National Oceanic and Atmospheric Administration (NOAA)"
        },
        {
            "subgenre": "ancient_mysteries",
            "title": "The Antikythera Mechanism: 2000-Year-Old Analog Computer",
            "hook": "Divers in 1901 pulled a bronze machine from a shipwreck that should not have existed for another thousand years.",
            "script_15s": "Inside a corroded lump of bronze, X-ray scans revealed over thirty interlocking precision gears. Built by ancient Greeks around 100 BC, the Antikythera mechanism calculated eclipse cycles, lunar phases, and the positions of five visible planets with flawless mechanical accuracy.",
            "script_30s": "Off the coast of Greece in 1901, sponge divers discovered a Roman shipwreck. Hidden inside was a heavily calcified bronze artifact. When archaeologists analyzed it with 3D X-ray tomography decades later, they were stunned. The Antikythera mechanism was an intricate analog computer with over thirty microscopic bronze gears. It accurately predicted solar eclipses, planetary movements, and Olympic Games calendars. Its mechanical sophistication disappeared from history for over a millennium.",
            "keywords": ["ancient", "bronze", "stone", "history", "ruins"],
            "badge": "📜 HISTORICAL ENIGMA",
            "theme": "deep_emerald",
            "source": "Nature / Antikythera Mechanism Research Project"
        }
    ],
    "informative": [
        {
            "subgenre": "critical_thinking",
            "title": "The Survivorship Bias of Bullet Holes",
            "hook": "Why reinforcing the most damaged parts of an airplane will guarantee it gets shot down.",
            "script_15s": "During World War II, military engineers examined returning bombers and planned to armor the areas covered in bullet holes. Statistician Abraham Wald stopped them: the planes shot in the engines never made it home to be counted. Look where the missing data is.",
            "script_30s": "During World War II, the military mapped where returning planes took the most bullet hits: the wings and fuselage. The top brass wanted to add heavy armor to those exact spots. But mathematician Abraham Wald realized a fatal blind spot: they were only examining the planes that survived. The planes that took hits to the engines and cockpit crashed into the sea. Armoring the bullet holes protects the spots that can survive damage. In life, always look for the data that did not return.",
            "keywords": ["airplane", "history", "military", "thinking", "strategy"],
            "badge": "🧠 COGNITIVE MODEL",
            "theme": "deep_emerald",
            "source": "Abraham Wald, Statistical Research Group (Columbia University)"
        },
        {
            "subgenre": "technology_analysis",
            "title": "The Dead Internet Theory",
            "hook": "Is the modern internet mostly automated bots talking to other automated bots?",
            "script_15s": "Recent cybersecurity audits reveal that nearly fifty percent of all global web traffic is generated by autonomous bots, scrapers, and artificial agents. The digital square is shifting from human conversation to synthetic engagement loops designed to farm algorithmic metrics.",
            "script_30s": "What started as an online fringe theory is rapidly becoming documented reality. Recent cybersecurity research shows that automated bots now account for nearly half of all web traffic worldwide. From algorithmic account engagement to automated comment generation, synthetic interactions are outnumbering human interactions on major platforms. Understanding this changes how you view content: digital engagement is no longer proof of human resonance.",
            "keywords": ["technology", "internet", "code", "robot", "digital"],
            "badge": "⚡ TECH AUDIT",
            "theme": "cyber_blue",
            "source": "Imperva Bad Bot Report & Cloudflare Insights"
        }
    ],
    "emotional": [
        {
            "subgenre": "perseverance_and_grit",
            "title": "The Twenty-Two Year Road of Dashrath Manjhi",
            "hook": "When a mountain took the love of his life, he spent twenty-two years carving a road through it alone.",
            "script_15s": "After his wife died because medical help was fifty miles around a mountain, Dashrath Manjhi sold three goats to buy a hammer and chisel. For twenty-two solitary years, he carved through rock, turning a fifty-mile detour into a four-mile road for his entire village.",
            "script_30s": "In 1959, in a remote Indian village, Dashrath Manjhi lost his injured wife because the nearest hospital lay fifty miles away around an impassable rocky mountain. Heartbroken, he took a simple hammer and chisel and began striking the rock. Neighbors called him insane. For twenty-two years, in blinding heat and bitter cold, he carved through three hundred feet of solid stone. By 1982, he had cut a road through the mountain, reducing the hospital distance to four miles and saving thousands of future lives.",
            "keywords": ["mountain", "stone", "nature", "walk", "inspiration"],
            "badge": "❤️ TRUE COURAGE",
            "theme": "crimson_flame",
            "source": "Documented Biography of Dashrath Manjhi"
        },
        {
            "subgenre": "friendship_and_loyalty",
            "title": "Hachiko: Ten Years on the Platform",
            "hook": "Every afternoon at 3 PM, an Akita dog waited at the train station for a master who never returned.",
            "script_15s": "When Professor Ueno suffered a fatal stroke at Tokyo University in 1925, his faithful dog Hachiko returned to Shibuya Station every single afternoon for nine years, nine months, and fifteen days. True loyalty is not bounded by time or absence.",
            "script_30s": "In Tokyo, Professor Hidesaburo Ueno took the train to university every morning, and his Akita dog Hachiko walked beside him to Shibuya Station, waiting for his return at 3 PM. In May 1925, the professor died unexpectedly at work. Hachiko showed up at the station that afternoon, and the next afternoon, and every single afternoon for nearly ten years through snow, rain, and heat. Commuters fed him, and today a bronze statue stands where true loyalty lived.",
            "keywords": ["dog", "train", "station", "city", "friendship"],
            "badge": "🐕 TIMELESS LOYALTY",
            "theme": "deep_emerald",
            "source": "Historical Shibuya City Archives"
        }
    ],
    "storytelling": [
        {
            "subgenre": "sci_fi_twist",
            "title": "The Last Signal From Deep Space",
            "hook": "In 2042, humanity's deepest probe detected a rhythmic radio signal originating from our own solar system.",
            "script_15s": "The transmission was pinpointed to an ancient metallic object buried beneath Europa's ice sheet. When linguists finally translated the first eight binary words, the entire scientific council went dead silent. The message read: 'Do not reply. They are still searching.'",
            "script_30s": "In 2042, the deep-space probe Prometheus picked up an artificial beacon coming from the outer rim of our solar system. It was not static; it was a compressed repeating binary signal. When cryptographers at MIT decoded the header, they discovered the transmitter had been active for two million years. The translated sentence sent chills through the observatory: 'To whatever civilization hears this: turn off your radio emissions immediately. The hunters are listening.'",
            "keywords": ["space", "cosmos", "stars", "planet", "galaxy"],
            "badge": "🛸 SCI-FI NARRATIVE",
            "theme": "cosmic_purple",
            "source": "Speculative Sci-Fi Fiction"
        },
        {
            "subgenre": "suspense_mystery",
            "title": "The Clockmaker's Final Secret",
            "hook": "An antique clock that stopped ticking in 1912 suddenly chimed three times at midnight.",
            "script_15s": "The watchmaker opened the mahogany casing and found an intricate double escapement with no mainspring. Inside the hollow pendulum was a brass cylinder containing a handwritten note from his own grandfather, dated tomorrow morning.",
            "script_30s": "Arthur inherited his grandfather's dusty horology shop in London. In the back corner stood an ornate grandfather clock that had not ticked since 1912. But on the stroke of midnight, the bells rang with crystal clarity. Arthur removed the brass gearplate and found something that violated physics: the gears were made of an unknown alloy that showed zero friction wear. Behind the pendulum sat a sealed envelope addressed to him in fresh ink, dated tomorrow.",
            "keywords": ["clock", "antique", "dark", "mystery", "wood"],
            "badge": "⏳ SUSPENSE TALE",
            "theme": "cosmic_purple",
            "source": "Atmospheric Narrative Fiction"
        }
    ],
    "animation": [
        {
            "subgenre": "cartoon_comedy_skit",
            "title": "The Alarm Clock vs The Human Brain",
            "hook": "An animated battle between your Alarm Clock and your Prefrontal Cortex at 6:00 AM.",
            "script_15s": "Alarm Clock: 'Wake up! It is time to conquer your goals!' Brain: 'Counterpoint: the blanket is at exactly 98.6 degrees and reality is loud.' Snooze button: 'Allow me to introduce ten minutes of pure bliss.'",
            "script_30s": "Meet Alarm Clock, an energetic metallic lunatic screaming at 6:00 AM sharp: 'Rise and shine, champion!' Meanwhile, inside the skull, Brain is negotiating a peace treaty with Pillow. 'If we stay asleep, no awkward small talk with coworkers, no cold floors, just pure warmth.' Snooze button slides in like a shady diplomat: 'Just hit me once. What could possibly go wrong in nine minutes?'",
            "keywords": ["clock", "bed", "sleeping", "funny", "cartoon"],
            "badge": "🎨 ANIMATED SKIT",
            "theme": "cyber_blue",
            "source": "Original Animated Comedy Short"
        },
        {
            "subgenre": "character_dialogue",
            "title": "The Procrastination Demon and The To-Do List",
            "hook": "What happens when your To-Do List confronts the Procrastination Monster.",
            "script_15s": "To-Do List: 'We have three urgent deadlines due in two hours!' Procrastination Monster: 'Yes, but have you considered researching the history of 14th-century Estonian medieval pottery right now instead?'",
            "script_30s": "To-Do List stands tall with three bold bullet points: Finish presentation, submit taxes, email landlord. Enter the Procrastination Monster, holding an iPad with seventeen open tabs. 'Sure, those are important, but did you know sharks were around before trees? Let us watch a forty-minute documentary about deep-sea trench construction instead.' Brain nods enthusiastically: 'This is essential research!'",
            "keywords": ["office", "computer", "desk", "cartoon", "technology"],
            "badge": "👾 CHARACTER BATTLE",
            "theme": "crimson_flame",
            "source": "Original Character Cartoon"
        }
    ],
    "cinematic": [
        {
            "subgenre": "dramatic_monologue",
            "title": "The Silence Before The Storm",
            "hook": "They told him the odds were zero. That was the moment he stopped asking for permission.",
            "script_15s": "The room went dead quiet. In the final seconds before launch, doubt disappears and only resolve remains. Greatness is not born in the spotlight; it is forged in the silence where you decide not to turn back.",
            "script_30s": "Every great breakthrough in human history was preceded by an army of critics shouting that it could not be done. In the quiet dark before dawn, when the monitors glow and the heartbeat echoes in your ears, the noise of the world fades away. You do not achieve the impossible by waiting for consensus. You achieve it by taking the one step everyone else was too terrified to take.",
            "keywords": ["dramatic", "city", "skyline", "night", "dark"],
            "badge": "🎬 CINEMATIC EDIT",
            "theme": "crimson_flame",
            "source": "Cinematic Inspirational Monologue"
        },
        {
            "subgenre": "trailer_tension",
            "title": "Project Eclipse: The Countdown",
            "hook": "T-minus twenty seconds. All telemetry systems report go, but the core telemetry is shifting.",
            "script_15s": "Steam vents hiss across the launchpad. The horizon glows in deep crimson. When the engines ignite, there is no contingency plan. You either break orbit, or you become part of the atmosphere.",
            "script_30s": "Launch control: audio check, primary ignition confirmed. The heavy vibration rattles the cockpit steel as twenty million pounds of thrust shake the coastline. The horizon tilts into deep indigo, then pure black. Earth curves below like a blue jewel against infinite dark. You are no longer tethered to gravity. You are walking into the deep unknown.",
            "keywords": ["space", "fire", "launch", "dramatic", "stars"],
            "badge": "🚀 ACTION MONTAGE",
            "theme": "crimson_flame",
            "source": "Trailer-Style Action Sequence"
        }
    ]
}

def get_catalog_topics(genre: Optional[str] = None, subgenre: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns topics matching genre and subgenre.
    """
    if genre and genre in GENRE_TOPICS_DATABASE:
        topics = GENRE_TOPICS_DATABASE[genre]
        if subgenre:
            matched = [t for t in topics if t.get("subgenre") == subgenre]
            return matched if matched else topics
        return topics

    all_topics = []
    for g, items in GENRE_TOPICS_DATABASE.items():
        for item in items:
            c = item.copy()
            c["genre"] = g
            all_topics.append(c)
    return all_topics

def list_all_genres_info() -> Dict[str, Any]:
    from .creative_randomizer import GENRE_TAXONOMY
    return GENRE_TAXONOMY

