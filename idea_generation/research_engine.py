"""
Autonomous Idea Research & Creative Engine for AutoReelStudio.
Generates industry-grade, high-retention vertical Reel concepts across:
  1. System Design & Distributed Systems (Kafka, Redis, Sharding, Consistent Hashing)
  2. Computer Engineering & Silicon Hardware (CPU Branch Prediction, Cache Hierarchy, GPU SIMD)
  3. Study Shorts & Computer Science Concepts (Big-O Complexity, Stack vs Heap, Compilers)
  4. Scientific Facts & Deep Cosmos Paradoxes (Earth Mantle Ocean, Cold Plasma, Quantum Eraser, Boötes Void)
  5. Deep Tech & Ancient Engineering Mysteries (Roman Concrete, Antikythera Computer, $18M NASA Typo)
"""

import hashlib
import random
import time
from typing import Dict, Any, List, Optional
from .feedback_learner import FeedbackLearner

RESEARCH_DOMAINS = {
    "system_design": [
        {
            "topic": "How Kafka Handles 10 Million Writes/Sec with Zero-Copy",
            "hook": "How does Apache Kafka write 10 million messages a second without melting your CPU?",
            "facts": "Kafka doesn't write to disk through user-space buffers. It bypasses JVM memory entirely using the Linux sendfile() system call. Data transfers directly from OS PageCache to the Network Interface Card via Direct Memory Access (DMA), achieving zero-copy transfer with near-zero CPU overhead.",
            "payoff": "By treating the Linux kernel's pagecache as its database, Kafka turns cheap mechanical disks into in-memory speed demons.",
            "style": "system_design",
            "scenes": [
                {
                    "text": "How does Apache Kafka write 10 million messages a second without melting your CPU?",
                    "visual_prompt": "System design architecture diagram of high-throughput client producers sending sequential append-only write streams to Apache Kafka broker cluster, 9:16 vertical engineering layout, dark theme neon cyan and emerald, technical blueprint style",
                    "motion": "zoom_in"
                },
                {
                    "text": "Traditional databases copy data four times between user memory and kernel buffers. Kafka skips all of them.",
                    "visual_prompt": "Comparative architectural diagram of traditional JVM 4-copy context switch vs Linux kernel zero-copy sendfile pipeline, DMA direct memory access to NIC buffer, glowing circuit traces, 9:16 vertical layout",
                    "motion": "pan_right"
                },
                {
                    "text": "By treating the Linux OS PageCache as its memory cache, Kafka achieves memory-like speed directly on physical disk.",
                    "visual_prompt": "Key system design takeaway card highlighting Linux PageCache throughput metrics with 10M msg/s rate and sub-millisecond p99 latency gauge, crisp typography, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "Consistent Hashing: How Discord Scales Without Crashing",
            "hook": "What happens when a database node crashes with 50 million active users?",
            "facts": "In naive hashing hash(key) modulo N, adding or removing a single server forces 99% of all keys to relocate, causing massive cascading server outages. Consistent Hashing maps both servers and data keys to a 360-degree virtual ring. When a server dies, only K over N keys move to the next immediate neighbor.",
            "payoff": "This single mathematical ring prevents global downtime across Discord, DynamoDB, and Netflix every single day.",
            "style": "system_design",
            "scenes": [
                {
                    "text": "What happens when a database node crashes with 50 million active users on Discord?",
                    "visual_prompt": "System design diagram of distributed database cluster with a dead node causing catastrophic cascade rehash in traditional modulo hashing, dark UI with glowing red alerts, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "Consistent Hashing maps both physical servers and user data keys onto a 360-degree virtual circular ring.",
                    "visual_prompt": "Visual architecture diagram of 360-degree Consistent Hashing Virtual Ring with distributed nodes A, B, C, D and virtual token positions, glowing neon blue data points mapping clockwise, 9:16 vertical aspect ratio",
                    "motion": "pan_left"
                },
                {
                    "text": "When a node fails, only its immediate neighbor takes the load — saving the rest of the cluster from collapse.",
                    "visual_prompt": "System resilience metrics card showing zero-downtime key relocation at K/N efficiency, high-contrast engineering schematic, 9:16 vertical layout",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "Redis is Single-Threaded: How it Serves 100K Req/Sec",
            "hook": "Redis runs on a single CPU core, yet it outpaces multithreaded databases ten times its size.",
            "facts": "Redis avoids multithreading because mutex lock contention and thread context switching kill performance. Instead, it uses Linux epoll I/O multiplexing. A single non-blocking event loop handles thousands of concurrent socket connections entirely in L3 cache without a single thread lock.",
            "payoff": "In low-latency memory systems, avoiding lock contention is faster than throwing 64 CPU cores at the problem.",
            "style": "system_design",
            "scenes": [
                {
                    "text": "Redis runs on a single CPU core, yet it outpaces multithreaded databases ten times its size.",
                    "visual_prompt": "System design comparison card of multithreaded thread lock contention vs Redis single-threaded event loop, dark mode engineering UI with neon orange and cyan, 9:16 vertical aspect ratio",
                    "motion": "zoom_in"
                },
                {
                    "text": "Using Linux epoll I/O multiplexing, a single thread monitors thousands of non-blocking client sockets simultaneously.",
                    "visual_prompt": "Technical architectural flowchart showing incoming socket descriptors multiplexed through Linux epoll event loop directly into in-memory dictionary and skiplist data structures, 9:16 vertical layout",
                    "motion": "pan_right"
                },
                {
                    "text": "Because everything stays in high-speed CPU cache without mutex locks, operations complete in sub-millisecond time.",
                    "visual_prompt": "Redis performance benchmark dashboard card showing 120,000 ops/sec throughput and 0.2ms latency with zero lock overhead, crisp JetBrains Mono typography, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "Bloom Filters: How Chrome Checks 1 Billion URLs in 1ms",
            "hook": "How can your browser check if a URL is malicious out of 1 billion websites without a database lookup?",
            "facts": "A Bloom Filter is a space-efficient probabilistic data structure. A URL is hashed through multiple independent hash functions to set specific bits in an array to 1. If any bit is 0, the URL is guaranteed 100% safe. Disk queries only happen for the tiny fraction of false positives.",
            "payoff": "A tiny 100-megabyte bit array protects your browser against a 50-gigabyte database of dangerous websites.",
            "style": "system_design",
            "scenes": [
                {
                    "text": "How can your browser check if a URL is malicious out of 1 billion websites without searching a database?",
                    "visual_prompt": "Engineering security diagram of incoming web URL passing through client browser security gateway, dark aesthetic with glowing cyan security shields, 9:16 vertical format",
                    "motion": "zoom_in"
                },
                {
                    "text": "A Bloom Filter runs the URL through independent hash functions, setting specific indexes in a compact bit array.",
                    "visual_prompt": "Technical diagram of 3 independent hash functions (h1, h2, h3) mapping into a glowing binary bit array of 0s and 1s, probabilistic data structure visualization, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "If even one bit is zero, the URL is guaranteed safe in 1 millisecond without touching disk.",
                    "visual_prompt": "High-efficiency memory comparison card: 100MB RAM bit array vs 50GB disk database query reduction, crisp technical specifications, 9:16 vertical layout",
                    "motion": "zoom_out"
                }
            ]
        }
    ],

    "computer_engineering": [
        {
            "topic": "CPU Branch Prediction: Why Sorted Data Runs 6x Faster",
            "hook": "Your CPU runs faster when your data is sorted — and the reason is an invisible crystal ball inside the silicon.",
            "facts": "Modern CPU pipelines are 15 to 20 stages deep. When code reaches an if statement, waiting for the memory lookup wastes 20 clock cycles. The Branch Predictor uses history tables to guess the outcome. If correct, execution flows seamlessly at 4 billion instructions per second.",
            "payoff": "Sorting an array makes an unsorted loop run six times faster, purely by feeding the CPU predictor clean patterns.",
            "style": "computer_engineering",
            "scenes": [
                {
                    "text": "Your CPU runs faster when your data is sorted — and the reason is an invisible crystal ball inside the silicon.",
                    "visual_prompt": "Micro-architecture silicon die schematic showing CPU instruction pipeline with fetch, decode, and speculative execution units, dark carbon background with glowing amber traces, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "CPUs use 2-level adaptive history tables to predict which branch your code will take before executing it.",
                    "visual_prompt": "Hardware schematic of 2-Level Adaptive Branch History Table mapping branch addresses to 2-bit saturating counters (Strongly Taken, Weakly Taken), technical silicon blueprint, 9:16 vertical format",
                    "motion": "pan_left"
                },
                {
                    "text": "When data is sorted, predictions hit 99% accuracy — eliminating catastrophic 20-cycle pipeline flushes.",
                    "visual_prompt": "Benchmark card comparing unsorted array (11.8s, 20% branch misses) vs sorted array (1.9s, 0.1% branch misses) with assembly instructions, crisp JetBrains Mono font, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "False Sharing: The Hardware Glitch Killing Multithreading",
            "hook": "You added 8 CPU threads to make your program faster, and it ran ten times slower. Here is why.",
            "facts": "CPUs do not read single bytes from RAM; they fetch 64-byte chunks called Cache Lines. If Thread 1 on Core 0 modifies Variable A, and Thread 2 on Core 1 modifies independent Variable B right next to it, the hardware invalidates the entire cache line across all cores via MESI protocol.",
            "payoff": "The CPU cores spend 95% of their time fighting over cache coherence buses instead of doing actual computation.",
            "style": "computer_engineering",
            "scenes": [
                {
                    "text": "You added 8 CPU threads to make your program faster, and it ran ten times slower. Here is why.",
                    "visual_prompt": "Hardware architecture diagram showing dual CPU cores competing over shared memory cache line, glowing red conflict arrows and bus lock contention, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "CPUs move memory in 64-byte cache lines. If two threads touch adjacent variables, the hardware invalidates the line on every write.",
                    "visual_prompt": "Technical memory diagram of a 64-byte cache line split between Variable A and Variable B, showing MESI cache coherence protocol invalidation ping-pong, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "Adding simple memory padding between variables separates the cache lines and restores 8x multithreaded scaling.",
                    "visual_prompt": "Optimization comparison card showing struct alignment with alignas(64) cache line padding restoring linear thread scaling, crisp monospace code, 9:16 vertical layout",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "Virtual Memory & The TLB: The 64-Bit Pointer Illusion",
            "hook": "Your computer thinks every program owns 128 Terabytes of RAM, even if you only bought 16 Gigabytes.",
            "facts": "Every memory address in user space is virtual. The CPU Memory Management Unit (MMU) walks a 4-level page table to map virtual pages to physical DRAM frames. To avoid 4 memory lookups on every single pointer, the Translation Lookaside Buffer (TLB) caches translations in single-cycle silicon.",
            "payoff": "Virtual memory isolates processes so a crash in Chrome cannot corrupt your operating system kernel.",
            "style": "computer_engineering",
            "scenes": [
                {
                    "text": "Your computer thinks every program owns 128 Terabytes of RAM, even if you only bought 16 Gigabytes.",
                    "visual_prompt": "Computer engineering visual showing 64-bit virtual address space illusion mapping into physical DDR5 RAM modules, dark theme with glowing cyan page tables, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "The Memory Management Unit walks a 4-level page table to translate every virtual pointer to physical DRAM.",
                    "visual_prompt": "Hardware architecture diagram of 4-Level Page Table Walk: PML4 to Page Directory Pointer to Page Directory to Physical Page Frame, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "The Translation Lookaside Buffer caches these translations in single-cycle hardware, enabling blazing pointer access.",
                    "visual_prompt": "Latency hierarchy card: TLB Hit (0.5ns, 1 cycle) vs 4-Level Page Walk (60ns, 200 cycles) with memory isolation security guarantees, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        }
    ],

    "study_shorts": [
        {
            "topic": "Big-O Time Complexity: Why O(N²) Destroys Production",
            "hook": "The difference between O(1) and O(N²) is the difference between 1 millisecond and 30,000 years.",
            "facts": "For 1,000 items, an O(N) algorithm runs 1,000 operations. But an O(N²) nested loop runs 1 million operations. At 1 million items, O(N) takes 1 millisecond, while O(N²) takes 1 trillion operations — freezing your server forever.",
            "payoff": "Always replace nested loops with Hash Maps to transform O(N²) operations into O(1) lookups.",
            "style": "study_shorts",
            "scenes": [
                {
                    "text": "The difference between O(1) and O(N²) is the difference between 1 millisecond and 30,000 years.",
                    "visual_prompt": "Mathematical Big-O time complexity graph showing O(1) green flat line, O(log N) cyan curve, O(N) yellow diagonal, and O(N²) red vertical spike, dark grid background, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "For one million items, an O(N) algorithm finishes in a millisecond. An O(N²) nested loop requires one trillion operations.",
                    "visual_prompt": "Scaling comparison table card displaying exact runtime benchmarks across 1,000, 100,000, and 1,000,000 elements for each complexity class, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "Replacing nested iteration with a single Hash Map lookup transforms an exponential freeze into an instant O(1) response.",
                    "visual_prompt": "Code optimization card with before/after Python/JavaScript snippet showing nested loops replaced with O(1) dictionary lookup, crisp JetBrains Mono code, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "Stack vs Heap Memory: The Real Cause of StackOverflow",
            "hook": "Why does infinite recursion cause a StackOverflow, but memory leaks happen on the Heap?",
            "facts": "The Stack is ultra-fast, contiguous LIFO memory managed automatically by the CPU stack pointer for local variables and return addresses. The Heap is dynamic, fragmented memory allocated at runtime via malloc. When deep recursion exceeds stack bounds, the stack pointer collides with protected memory.",
            "payoff": "Use tail-call optimization or iterative loops with heap data structures to process deep recursive trees safely.",
            "style": "study_shorts",
            "scenes": [
                {
                    "text": "Why does infinite recursion cause a StackOverflow, but memory leaks happen on the Heap?",
                    "visual_prompt": "Memory layout diagram of a process address space showing Stack growing downward and Heap growing upward toward each other, dark theme neon purple and blue, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "The Stack is ultra-fast LIFO memory tracked by a single CPU register. When recursive frames pile up, it smashes into the guard page.",
                    "visual_prompt": "Detailed visualization of Stack Frame activation records: return address, base pointer, and local variables overflowing into memory fault boundary, 9:16 vertical format",
                    "motion": "pan_left"
                },
                {
                    "text": "Heap memory gives you dynamic size at the cost of fragmentation, while Stack memory gives you pure hardware speed.",
                    "visual_prompt": "Engineering summary card comparing Stack (1-cycle, auto-freed, 8MB max) vs Heap (pointer lookup, fragmented, gigabytes), crisp typography, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        }
    ],

    "science_paradoxes": [
        {
            "topic": "The Ocean Floating 400 Miles Under Earth's Crust",
            "hook": "There is a hidden ocean inside Earth holding three times more water than all surface oceans combined.",
            "facts": "400 miles beneath North America, seismic data revealed water trapped inside a rare blue mineral called ringwoodite. It doesn't slosh around as liquid; it exists as hydroxide ions locked within the crystal lattice under 1,000 degrees heat and 200,000 atmospheres of pressure.",
            "payoff": "This discovery proves Earth's surface oceans didn't arrive via comets — they literally seeped out from inside our own mantle.",
            "style": "science_paradoxes",
            "scenes": [
                {
                    "text": "There is a hidden ocean inside Earth holding three times more water than all surface oceans combined.",
                    "visual_prompt": "Seismic geological cross-section diagram of planet Earth showing crust, upper mantle, glowing blue transition zone at 410-660km depth, outer core, and inner core, 9:16 vertical format",
                    "motion": "zoom_in"
                },
                {
                    "text": "Trapped four hundred miles down inside glowing blue ringwoodite crystals, water is locked at molecular scale under extreme pressure.",
                    "visual_prompt": "Scientific mineralogy diagram showing hydrous ringwoodite crystal lattice holding hydroxide ions under 200,000 atmospheres of pressure, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "This means Earth's oceans did not arrive on icy comets — they were born right inside our own planet's core.",
                    "visual_prompt": "Discovery summary card explaining how primordial mantle degassing seeded all surface oceans with depth and pressure telemetry, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "The Cold Plasma Flame That Doesn't Burn Skin",
            "hook": "Scientists created a flame so cold you can literally hold it in your bare hand.",
            "facts": "Non-thermal atmospheric plasma operates at 25 degrees Celsius. Because electric fields accelerate tiny electrons to high energies while leaving heavy atoms and ions at room temperature, it destroys 99.9% of bacteria and viruses in seconds without harming human tissue.",
            "payoff": "Hospitals are using cold purple plasma to sterilize deep surgical wounds and accelerate cellular tissue regeneration.",
            "style": "science_paradoxes",
            "scenes": [
                {
                    "text": "Scientists created a flame so cold you can literally hold it in your bare hand.",
                    "visual_prompt": "Scientific physics diagram of non-thermal atmospheric cold plasma torch operating at 25 degrees Celsius with violet ionized arc, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "Electrons accelerate to extreme velocities while heavy gas atoms stay at room temperature, creating non-thermal ionization.",
                    "visual_prompt": "Physics diagram illustrating electron temperature (Te >> Ti) vs heavy ion temperature in non-thermal atmospheric pressure plasma discharge, 9:16 vertical format",
                    "motion": "pan_left"
                },
                {
                    "text": "It can sterilize deep surgical wounds and kill bacteria in seconds without causing any tissue damage or pain.",
                    "visual_prompt": "Medical bio-technology card detailing hospital sterilization applications and reactive oxygen species bacteria disruption, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "The Quantum Eraser That Rewrites The Past",
            "hook": "Physicists built an experiment that proves a photon's past can be changed after it already landed.",
            "facts": "In the Delayed Choice Quantum Eraser experiment, particles act as waves when paths are unknown, but collapse into solid particles if measurement info is preserved — even if that measurement happens AFTER the particle hits the sensor.",
            "payoff": "At the quantum scale, time is not a one-way street — the future literally decides what the past did.",
            "style": "science_paradoxes",
            "scenes": [
                {
                    "text": "Physicists built an experiment that proves a photon's past can be changed after it already landed.",
                    "visual_prompt": "Quantum optics schematic diagram showing laser beam splitter, BBO crystal, and entangled signal and idler photon paths, 9:16 vertical format",
                    "motion": "zoom_in"
                },
                {
                    "text": "When researchers erase the measurement data, photons that already registered as particles instantly rewrite their behavior into waves.",
                    "visual_prompt": "Physics diagram of double-slit wave interference pattern vs particle collapse distribution with coincidence counter array, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "At the quantum scale, time is not a one-way street — the future literally decides what the past did.",
                    "visual_prompt": "Quantum physics takeaway card explaining retroactive causality and Wheeler's delayed choice paradox with mathematical equations, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "The Boötes Void: The 330 Million Light-Year Abyss",
            "hook": "There is an empty sphere in the cosmos 330 million light-years across that should contain 10,000 galaxies — but contains almost nothing.",
            "facts": "Discovered in 1981, the Boötes Supervoid is so massive that if the Milky Way were at its center, humanity wouldn't have discovered other galaxies until the 1960s with radio telescopes. Astronomers believe smaller cosmic voids merged like soap bubbles.",
            "payoff": "It remains the largest supervoid in the observable universe, a silent reminder of how vast and empty reality truly is.",
            "style": "science_paradoxes",
            "scenes": [
                {
                    "text": "There is an empty sphere in the cosmos 330 million light-years across that should contain 10,000 galaxies — but contains almost nothing.",
                    "visual_prompt": "Cosmological astrophysics map of the SDSS cosmic filament web showing the massive empty circular Boötes Supervoid surrounded by galaxy clusters, 9:16 vertical layout",
                    "motion": "zoom_in"
                },
                {
                    "text": "Spanning over 330 million light-years, it should hold thousands of Milky-Way sized galaxies, but astronomers found only sixty.",
                    "visual_prompt": "Scale comparison diagram comparing the Boötes Void volume (330 million light years) against the Local Group and Virgo Supercluster, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "If humanity lived in its center, we would have believed our galaxy was the only thing in the entire universe.",
                    "visual_prompt": "Cosmic telemetry card detailing void soap-bubble merger mechanics and dark energy expansion dynamics, crisp typography, 9:16 vertical layout",
                    "motion": "zoom_out"
                }
            ]
        }
    ],

    "ancient_mysteries": [
        {
            "topic": "Why Roman Concrete Gets Stronger Over 2,000 Years",
            "hook": "Ancient Roman harbors have been battered by ocean waves for 2,000 years — and they are harder today than when they were built.",
            "facts": "MIT geologists discovered Romans mixed quicklime at extreme temperatures, leaving microscopic lime clasts. When seawater cracks the concrete, it dissolves the lime, precipitating calcium carbonate that literally heals the cracks in real time.",
            "payoff": "Modern concrete crumbles in 50 years, but ancient Roman chemistry engineered self-healing stone that outlives empires.",
            "style": "ancient_mysteries",
            "scenes": [
                {
                    "text": "Ancient Roman harbors have been battered by ocean waves for 2,000 years — and they are harder today than when they were built.",
                    "visual_prompt": "Archaeological engineering schematic of ancient Roman marine concrete breakwater submerged under Mediterranean waves, 9:16 vertical format",
                    "motion": "zoom_in"
                },
                {
                    "text": "Romans used hot-mixing with volcanic pozzolana and quicklime, embedding reactive lime clasts throughout the mortar.",
                    "visual_prompt": "Microscopic mineralogy diagram showing calcium-rich lime clasts dissolving in seawater to precipitate aluminous tobermorite crystals, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "When seawater cracks the wall, the lime dissolves and crystallizes, self-healing the concrete forever.",
                    "visual_prompt": "Chemical engineering comparison card: modern Portland cement (50-year lifespan) vs Roman self-healing marine concrete (2,000-year durability), 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        },
        {
            "topic": "The Antikythera Mechanism: A 2,000-Year-Old Analog Computer",
            "hook": "In 1901, divers found a rusted lump of bronze that contained gear mechanisms modern humans couldn't build until the 1700s.",
            "facts": "Recovered from a Greek shipwreck, X-ray tomography revealed the Antikythera mechanism contained over 30 precision bronze gears. It calculated lunar phases, solar eclipses, planetary orbits, and the 4-year Olympic games cycle with differential gearing.",
            "payoff": "Greek engineering had invented the analog computer two millennia before Charles Babbage and Alan Turing.",
            "style": "ancient_mysteries",
            "scenes": [
                {
                    "text": "In 1901, divers found a rusted lump of bronze that contained gear mechanisms modern humans couldn't build until the 1700s.",
                    "visual_prompt": "Mechanical engineering schematic of the 2,000-year-old Antikythera Mechanism bronze differential gear train recovered from shipwreck, 9:16 vertical format",
                    "motion": "zoom_in"
                },
                {
                    "text": "CT scans revealed over thirty interlocking bronze gear wheels that calculated celestial orbits and predicted solar eclipses.",
                    "visual_prompt": "X-ray computed tomography mechanical breakdown showing Metonic calendar spiral and epicyclic lunar anomaly differential gears, 9:16 vertical format",
                    "motion": "pan_right"
                },
                {
                    "text": "Ancient Greek engineers had built the world's first analog computer two thousand years before the industrial revolution.",
                    "visual_prompt": "Historical tech timeline card contrasting the Antikythera computer (150 BC) against 18th-century Swiss clockwork and modern Babbage engines, 9:16 vertical format",
                    "motion": "zoom_out"
                }
            ]
        }
    ]
}

class IdeaResearchEngine:
    """Generates viral, deeply factual educational and engineering Reel concepts."""

    @classmethod
    def generate_creative_idea(
        cls,
        genre: Optional[str] = None,
        duration: int = 35,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a fact-checked, high-yield reel idea across System Design,
        Computer Engineering, CS Study Shorts, and Deep Science Paradoxes.
        """
        # Handle custom user prompt
        if custom_prompt and custom_prompt.strip():
            return cls._synthesize_from_custom_prompt(custom_prompt.strip(), duration)

        # Select domain
        available_domains = list(RESEARCH_DOMAINS.keys())
        # Balanced weights: 30% system_design, 25% computer_engineering, 25% study_shorts, 20% science_paradoxes
        weights = [0.30, 0.25, 0.25, 0.15, 0.05]

        if genre and genre in RESEARCH_DOMAINS:
            domain_key = genre
        else:
            domain_key = random.choices(available_domains, weights=weights, k=1)[0]

        pool = RESEARCH_DOMAINS[domain_key]
        raw_concept = random.choice(pool)

        # Unique identifier
        seed_str = f"{raw_concept['topic']}_{duration}_{time.time()}_{random.random()}"
        idea_id = hashlib.sha256(seed_str.encode()).hexdigest()[:12]

        script_text = " ".join([s["text"] for s in raw_concept["scenes"]])

        voice_map = {
            "system_design": "en-US-ChristopherNeural",       # Authoritative, energetic, tech lead tone
            "computer_engineering": "en-US-BrianMultilingualNeural", # Crisp, intellectual hardware tone
            "study_shorts": "en-US-AndrewMultilingualNeural",        # Engaging, clear, high-retention instructor tone
            "science_paradoxes": "en-US-GuyNeural",                 # Deep, mysterious documentary tone
            "ancient_mysteries": "en-US-AndrewMultilingualNeural"
        }
        suggested_voice = voice_map.get(domain_key, "en-US-AndrewMultilingualNeural")

        return {
            "id": idea_id,
            "title": raw_concept["topic"],
            "genre": domain_key,
            "hook": raw_concept["hook"],
            "script": script_text,
            "scenes": raw_concept["scenes"],
            "facts": raw_concept.get("facts", ""),
            "payoff": raw_concept.get("payoff", ""),
            "visual_style": raw_concept.get("style", "system_design"),
            "suggested_voice": suggested_voice,
            "suggested_music": "cyber_pulse",
            "caption_style": "high_impact",
            "duration": duration,
            "created_at": time.time(),
            "status": "ready"
        }

    @classmethod
    def _synthesize_from_custom_prompt(cls, prompt: str, duration: int) -> Dict[str, Any]:
        """Dynamically crafts a 3-act viral script and technical diagram prompts from a user prompt."""
        idea_id = hashlib.sha256(f"{prompt}_{time.time()}".encode()).hexdigest()[:12]
        clean_title = prompt.strip()
        if len(clean_title) > 65:
            clean_title = clean_title[:62] + "..."

        p_lower = prompt.lower()
        if any(w in p_lower for w in ["kafka", "redis", "shard", "cache", "consistent hash", "bloom", "database", "system design", "microservice"]):
            genre = "system_design"
        elif any(w in p_lower for w in ["cpu", "cache", "branch", "memory", "gpu", "simd", "silicon", "hardware", "transistor", "dram", "ssd"]):
            genre = "computer_engineering"
        elif any(w in p_lower for w in ["big-o", "algorithm", "complexity", "stack", "heap", "compiler", "pointer", "rust", "c++", "study"]):
            genre = "study_shorts"
        else:
            genre = "science_paradoxes"

        scenes = [
            {
                "text": f"How does {clean_title} actually work under the hood?",
                "visual_prompt": f"System architecture and technical engineering diagram illustrating {clean_title}, 9:16 vertical layout, dark theme neon blueprints",
                "motion": "zoom_in"
            },
            {
                "text": f"Behind the scenes, the core mechanics optimize performance at the hardware and architectural level.",
                "visual_prompt": f"Detailed component breakdown and data-flow schematic for {clean_title}, glowing node connections, 9:16 vertical format",
                "motion": "pan_right"
            },
            {
                "text": f"Mastering this single pattern will transform how you design production software forever.",
                "visual_prompt": f"Key takeaway benchmark and optimization summary card for {clean_title}, crisp JetBrains Mono typography, 9:16 vertical layout",
                "motion": "zoom_out"
            }
        ]

        script_text = " ".join([s["text"] for s in scenes])

        return {
            "id": idea_id,
            "title": clean_title,
            "genre": genre,
            "hook": scenes[0]["text"],
            "script": script_text,
            "scenes": scenes,
            "facts": f"Technical breakdown of {clean_title} and core underlying systems principles.",
            "payoff": f"Understanding {clean_title} gives you an unfair advantage in engineering and systems design.",
            "visual_style": genre,
            "suggested_voice": "en-US-AndrewMultilingualNeural",
            "suggested_music": "cyber_pulse",
            "caption_style": "high_impact",
            "duration": duration,
            "created_at": time.time(),
            "status": "ready"
        }
