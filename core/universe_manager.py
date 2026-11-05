"""
Technical & Scientific Knowledge Hub Engine for AutoReelStudio.
Replaces legacy cartoon universes with 5 high-converting, high-retention technical domains:
  1. system_design: System Design & Distributed Systems
  2. computer_engineering: Computer Engineering & Silicon Architecture
  3. study_shorts: CS Study Shorts & Algorithm Complexities
  4. science_paradoxes: Science & Cosmos Paradoxes
  5. ancient_mysteries: Ancient Tech & Engineering Marvels

Maintains strict 3-act viral architecture:
  Act 1 (0-4s): High-retention technical hook / paradox
  Act 2 (5-20s): Visual schematic breakdown & mechanism
  Act 3 (21-28s): Real-world engineering takeaway & takeaway punchline
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "universe_state.json"

# ==============================================================================
# CANONICAL TECHNICAL & SCIENTIFIC DOMAINS
# ==============================================================================

UNIVERSES = {
    "system_design": {
        "id": "system_design",
        "title": "System Design & Distributed Systems",
        "category": "distributed_systems",
        "description": "High-throughput architecture breakdowns: Kafka Zero-Copy, Consistent Hashing, Redis epoll event loop, Bloom filters, and Sharding.",
        "cast": [
            {
                "id": "pagecache",
                "name": "OS PageCache",
                "species": "Kernel Architecture",
                "traits": "Direct Memory Access (DMA) bypassing user-space JVM context switches"
            },
            {
                "id": "hash_ring",
                "name": "Consistent Ring",
                "species": "Virtual Topology",
                "traits": "360-degree virtual token ring balancing nodes with zero cascading outages"
            },
            {
                "id": "epoll",
                "name": "epoll Event Loop",
                "species": "I/O Multiplexing",
                "traits": "Non-blocking O(1) single-threaded demultiplexer serving 100K ops/sec"
            },
            {
                "id": "bloom",
                "name": "Bloom Filter",
                "species": "Probabilistic Sets",
                "traits": "Bit array with k hash functions; 0% false negatives in 1ms"
            }
        ],
        "default_voice": "en-US-ChristopherNeural",
        "episodes": [
            {
                "title": "Kafka Zero-Copy: 10 Million Writes/Sec",
                "hook": "How does Apache Kafka write 10 million messages a second without melting your CPU?",
                "act1": "Kafka doesn't write to disk through user-space buffers. It bypasses JVM memory entirely using the Linux sendfile() system call.",
                "act2": "Data transfers directly from OS PageCache to the Network Interface Card via Direct Memory Access (DMA), achieving zero-copy transfer with near-zero CPU overhead.",
                "act3": "By treating the Linux kernel's pagecache as its database, Kafka turns cheap mechanical disks into in-memory speed demons.",
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
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            },
            {
                "title": "Consistent Hashing: How Discord Scales",
                "hook": "What happens when a database node crashes with 50 million active users?",
                "act1": "In naive hashing hash(key) modulo N, adding or removing a single server forces 99% of all keys to relocate, causing massive cascading server outages.",
                "act2": "Consistent Hashing maps both servers and data keys to a 360-degree virtual ring. When a server dies, only K over N keys move to the next immediate neighbor.",
                "act3": "This single mathematical ring prevents global downtime across Discord, DynamoDB, and Netflix every single day.",
                "scenes": [
                    {
                        "text": "What happens when a database node crashes with 50 million active users?",
                        "visual_prompt": "System design architecture diagram of a high-scale microservices cluster under massive traffic spike, glowing server rack nodes connected via fiber lines, 9:16 vertical layout, dark engineering theme",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Naive modulo hashing forces 99% of keys to relocate. Consistent Hashing maps nodes to a virtual 360-degree ring.",
                        "visual_prompt": "Consistent Hashing 360-degree circular hash ring diagram, server nodes mapped at hash angles with virtual token positions and key partitions, neon cyan glow on dark background, 9:16 vertical format",
                        "motion": "pan_left"
                    },
                    {
                        "text": "When a node fails, only its immediate neighbor takes the load. Zero cascading crashes.",
                        "visual_prompt": "System topology diagram showing single node failover where only adjacent partition keys smoothly re-route to neighboring replica, high availability green indicator, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            },
            {
                "title": "Redis Single-Threaded: 100K Req/Sec",
                "hook": "Why is Redis single-threaded yet capable of handling 100,000 requests per second?",
                "act1": "Multithreading isn't free. In multi-threaded databases, up to 40% of CPU cycles are wasted on thread context switching and lock contention.",
                "act2": "Redis avoids locks completely by executing entirely in-memory and demultiplexing network sockets with Linux epoll. A single thread handles thousands of open connections sequentially.",
                "act3": "Because memory lookups take nanoseconds, waiting for locks is the bottleneck, not CPU cores. Simplicity wins.",
                "scenes": [
                    {
                        "text": "Why is Redis single-threaded yet capable of handling 100,000 requests per second?",
                        "visual_prompt": "System design architecture diagram of Redis single-threaded event loop engine, multiplexing client sockets with Linux epoll, neon cyan glow on dark navy blueprint, 9:16 vertical layout",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Multi-threading wastes 40% of CPU on thread locks. Redis eliminates locking entirely by doing everything in memory.",
                        "visual_prompt": "Architectural comparison schematic showing multi-threaded lock contention overhead vs Redis non-blocking epoll event demultiplexer, latency benchmarks, 9:16 vertical engineering layout",
                        "motion": "pan_right"
                    },
                    {
                        "text": "When memory access takes 100 nanoseconds, lock contention is the enemy, not core count.",
                        "visual_prompt": "Architecture summary card highlighting Redis 100,000 req/sec throughput, single-threaded execution pipeline, sub-millisecond p99 latency gauge, crisp monospace fonts, 9:16 vertical format",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            },
            {
                "title": "Bloom Filters: 1 Billion URLs in 1ms",
                "hook": "How does Google Chrome check if a URL is malicious out of 10 billion malicious links in under one millisecond?",
                "act1": "Storing 10 billion URLs would require hundreds of gigabytes of RAM Chrome simply doesn't have.",
                "act2": "Instead, Chrome uses a Bloom Filter: a tiny bit array with multiple mathematical hash functions. If any hashed bit is zero, the URL is guaranteed 100% safe without checking disk.",
                "act3": "A Bloom Filter can have false positives, but mathematically zero false negatives. 99% of safe requests never touch the database.",
                "scenes": [
                    {
                        "text": "How does Google Chrome check if a URL is malicious out of 10 billion links in under one millisecond?",
                        "visual_prompt": "System design architecture diagram showing browser security gateway filtering incoming URLs against a high-speed malicious domain filter, 9:16 vertical engineering blueprint",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Instead of full strings, a Bloom Filter runs the URL through three hash functions into a compact bit array.",
                        "visual_prompt": "Technical schematic of Bloom Filter algorithm: string hashed via Murmur3 into bit array indices with binary 0 and 1 bit registers, neon green indicators, 9:16 vertical layout",
                        "motion": "pan_left"
                    },
                    {
                        "text": "If any bit is zero, it is guaranteed safe. Zero false negatives, saving 99% of database queries.",
                        "visual_prompt": "Summary engineering card comparing Bloom Filter memory footprint (12 MB vs 50 GB) with 0% false negative guarantee, crisp monospace typography, 9:16 vertical format",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            }
        ]
    },

    "computer_engineering": {
        "id": "computer_engineering",
        "title": "Computer Engineering & Silicon Architecture",
        "category": "silicon_architecture",
        "description": "Low-level processor internals: Branch prediction, CPU cache lines, false sharing, virtual memory TLBs, and memory latency hierarchy.",
        "cast": [
            {
                "id": "branch_pred",
                "name": "Branch Predictor",
                "species": "Silicon Logic",
                "traits": "2-bit saturating counter branch target buffer predicting jump directions in 3ns"
            },
            {
                "id": "cache_line",
                "name": "64-Byte Cache Line",
                "species": "Memory Hierarchy",
                "traits": "L1/L2 hardware coherence protocol (MESI) cache unit"
            },
            {
                "id": "tlb",
                "name": "4-Level Page Table",
                "species": "MMU Silicon",
                "traits": "Hardware Translation Lookaside Buffer mapping 48-bit virtual space"
            },
            {
                "id": "out_of_order",
                "name": "OoO Execution Engine",
                "species": "CPU Micro-Op Scheduler",
                "traits": "Speculatively reorders machine instructions around memory latency stalls"
            }
        ],
        "default_voice": "en-US-GuyNeural",
        "episodes": [
            {
                "title": "CPU Branch Prediction: The Sorted Data Trick",
                "hook": "Why does sorting an array of numbers make the exact same loop run 6 times faster on modern CPUs?",
                "act1": "At the hardware level, modern CPUs have a 16-stage instruction pipeline. If the processor has to wait to see if an IF-statement is true or false, the entire pipeline stalls for up to 20 clock cycles.",
                "act2": "To stay at full speed, the CPU's silicon branch predictor guesses the outcome ahead of time. When data is sorted, branch patterns are predictable: all false, then all true.",
                "act3": "On unsorted data, the CPU mispredicts constantly, throwing away hundreds of partially executed instructions. Your code didn't change — the silicon's guesswork did.",
                "scenes": [
                    {
                        "text": "Why does sorting an array of numbers make the exact same loop run 6 times faster on modern CPUs?",
                        "visual_prompt": "Computer engineering hardware schematic: microprocessor instruction pipeline with fetch, decode, execute, and branch predictor units, dark silicon circuit board, neon cyan traces, 9:16 vertical layout",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "A modern CPU pipeline is 16 stages deep. When branch prediction fails, all 16 stages must be flushed.",
                        "visual_prompt": "Comparative hardware timing diagram: sorted array branch prediction hit rate (99%) vs unsorted pipeline flush penalty (20 cycles lost), neon red pipeline flush indicator, 9:16 vertical format",
                        "motion": "pan_left"
                    },
                    {
                        "text": "On sorted data, branch history matches 99% of jumps. The CPU executes speculatively at full hardware speed.",
                        "visual_prompt": "Engineering summary card: Branch Target Buffer 2-bit saturating counter state machine (Strongly Taken, Weakly Taken), 6x execution speedup benchmark chart, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            },
            {
                "title": "False Sharing: The Multithreading Hardware Glitch",
                "hook": "Why did adding 8 CPU threads make this multi-threaded C program run 10 times SLOWER than a single thread?",
                "act1": "CPUs do not read memory one byte at a time. Hardware fetches data in fixed 64-byte blocks called cache lines.",
                "act2": "When two threads on separate cores write to two completely independent variables that happen to share the same 64-byte cache line, the CPU hardware coherence protocol invalidates both L1 caches back and forth millions of times a second.",
                "act3": "This is False Sharing. The threads never touch each other's data, yet spend 90% of their time waiting for cache coherence signals. Aligning variables to 64 bytes fixes it instantly.",
                "scenes": [
                    {
                        "text": "Why did adding 8 CPU threads make this multi-threaded C program run 10 times SLOWER than a single thread?",
                        "visual_prompt": "Microprocessor dual-core architecture diagram: Core 0 and Core 1 with private L1 and L2 caches connected via MESI coherence bus, 9:16 vertical engineering layout, dark tech aesthetic",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "CPUs fetch memory in 64-byte cache lines. If two independent variables share one line, cores fight over ownership.",
                        "visual_prompt": "Hardware memory cache line breakdown diagram: single 64-byte L1 cache line containing Variable A (Core 0) and Variable B (Core 1) bouncing between cores with cache invalidation alerts, 9:16 vertical",
                        "motion": "pan_right"
                    },
                    {
                        "text": "By adding 64-byte memory padding, each thread gets its own cache line, restoring linear 8x parallel speedup.",
                        "visual_prompt": "Summary hardware engineering card showing alignas(64) cache-line padding fix and benchmark curve jumping from 0.8x to 7.9x throughput, clean monospace code, 9:16 vertical format",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            },
            {
                "title": "Virtual Memory & The TLB: The 64-Bit Pointer Illusion",
                "hook": "The memory address in your C pointer does not exist anywhere on your physical RAM stick.",
                "act1": "Every user-space program runs in an isolated 48-bit virtual address space. When you access address 0x7fff5fbff, the CPU's Memory Management Unit (MMU) must translate it into a physical RAM chip location.",
                "act2": "Without hardware optimization, every single pointer dereference would require walking a 4-level page table — 4 separate RAM accesses just to read one variable.",
                "act3": "The Translation Lookaside Buffer (TLB) caches these translations in dedicated ultra-fast silicon. When TLB misses occur, your CPU stalls waiting on physical bus cycles.",
                "scenes": [
                    {
                        "text": "The memory address in your C pointer does not exist anywhere on your physical RAM stick.",
                        "visual_prompt": "Hardware architecture schematic showing 64-bit virtual address space splitting into Page Directory and Offset fields, connected to CPU MMU silicon, 9:16 vertical layout, dark blueprint theme",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "The Memory Management Unit walks a 4-level hierarchical page table in physical DRAM to find the real frame.",
                        "visual_prompt": "4-level page table translation walkthrough diagram (PML4 -> PDPT -> PD -> PT -> Physical Frame), neon green address translation pathways, 9:16 vertical format",
                        "motion": "pan_left"
                    },
                    {
                        "text": "The Translation Lookaside Buffer caches these translations in 1-nanosecond silicon, making the illusion seamless.",
                        "visual_prompt": "Hardware engineering summary card: TLB cache hit rates (99.2%) vs Page Fault penalty (millions of cycles), memory latency hierarchy chart, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "cyber_pulse",
                "soundtrack_genre": "high_tech"
            }
        ]
    },

    "study_shorts": {
        "id": "study_shorts",
        "title": "CS Study Shorts & Algorithm Complexities",
        "category": "computer_science",
        "description": "Core computer science fundamentals: Big-O scaling, Stack vs Heap memory allocations, Compiler optimization tricks, and Data Structures.",
        "cast": [
            {
                "id": "big_o",
                "name": "Big-O Curves",
                "species": "Complexity Analysis",
                "traits": "Asymptotic upper bounds: O(1) constant vs O(N^2) quadratic explosion"
            },
            {
                "id": "stack",
                "name": "Stack Pointer (RSP)",
                "species": "LIFO Architecture",
                "traits": "Ultra-fast contiguous memory allocated via single pointer decrement"
            },
            {
                "id": "heap",
                "name": "Dynamic Heap",
                "species": "Memory Management",
                "traits": "Global memory pool with malloc/free fragmented block management"
            },
            {
                "id": "llvm",
                "name": "LLVM Optimizer",
                "species": "Compiler Passes",
                "traits": "SSA dead-code elimination, vectorization, and loop unrolling"
            }
        ],
        "default_voice": "en-US-EricNeural",
        "episodes": [
            {
                "title": "Big-O Time Complexity: O(N²) in Production",
                "hook": "Why does a nested loop that runs in 2 milliseconds on your laptop crash the server when 100,000 users log in?",
                "act1": "Big-O is not about raw speed — it is about scaling curves. An algorithm with O(N) linear complexity scales gracefully: 10 times more data means 10 times more work.",
                "act2": "An O(N²) nested loop squares the input. With 100 items, it performs 10,000 operations. With 100,000 items, it explodes to 10 billion operations.",
                "act3": "Replacing a nested lookup with a Hash Map drops complexity from O(N²) to O(N), shrinking hours of computation into 50 milliseconds.",
                "scenes": [
                    {
                        "text": "Why does a nested loop that runs in 2 milliseconds on your laptop crash the server when 100,000 users log in?",
                        "visual_prompt": "Mathematical Big-O Cartesian coordinate graph showing input size N on X-axis vs operations on Y-axis, plotting color-coded asymptotic curves for O(1), O(log N), O(N), and O(N^2), 9:16 vertical layout",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "O(N) scales in a straight line. O(N²) explodes exponentially into billions of wasted CPU cycles.",
                        "visual_prompt": "Comparative Cartesian graph highlighting steep red vertical explosion of O(N^2) curve vs smooth green O(N) line at N=100,000, algorithmic complexity chart, 9:16 vertical format",
                        "motion": "pan_left"
                    },
                    {
                        "text": "Replacing a nested array scan with an O(1) Hash Map reduces 10 billion operations to 100,000 instant lookups.",
                        "visual_prompt": "Algorithm optimization cheat sheet card comparing Array scan O(N) vs Hash Table lookup O(1), runtime comparison metrics from 4.2 hours to 48ms, crisp typography, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "educational"
            },
            {
                "title": "Stack vs Heap: The Real Cause of StackOverflow",
                "hook": "Where does your variable actually live when you declare it in Python or C?",
                "act1": "When a function runs, local variables are pushed onto the Stack. The CPU simply moves a register pointer (RSP) down by 8 bytes — allocation takes zero clock cycles.",
                "act2": "The Stack is tiny: typically only 8 Megabytes. If a recursive function calls itself infinitely, the stack pointer collides with protected memory, triggering a hardware SIGSEGV Stack Overflow.",
                "act3": "Large objects live on the Heap: a multi-gigabyte memory pool requiring dynamic allocation algorithms and garbage collection. Speed lives on the Stack; scale lives on the Heap.",
                "scenes": [
                    {
                        "text": "Where does your variable actually live when you declare it in Python or C?",
                        "visual_prompt": "Computer science memory architecture diagram: virtual memory space divided into Stack (growing downward) and Heap (growing upward) with unallocated space in between, 9:16 vertical layout",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Stack allocation is instant because the CPU only adjusts the RSP pointer. But the stack is capped at 8 megabytes.",
                        "visual_prompt": "Detailed memory stack frame walkthrough showing function activation records (Return Address, Saved RBP, Local Variables), RSP stack pointer animation, 9:16 vertical format",
                        "motion": "pan_right"
                    },
                    {
                        "text": "When recursion exceeds 8 MB, stack memory collides with protected pages, throwing a hardware Stack Overflow.",
                        "visual_prompt": "Summary CS concept card comparing Stack (LIFO, 8MB, nanosecond speed) vs Heap (dynamic pool, gigabytes, fragmentation), key interview takeaway, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "educational"
            }
        ]
    },

    "science_paradoxes": {
        "id": "science_paradoxes",
        "title": "Science & Cosmos Paradoxes",
        "category": "physics_cosmology",
        "description": "Mind-bending physical phenomena: Earth's 400-mile deep mantle ocean, Cold Atmospheric Plasma, the Quantum Eraser, and Boötes Void.",
        "cast": [
            {
                "id": "ringwoodite",
                "name": "Ringwoodite Crystal",
                "species": "Mantle Mineral",
                "traits": "Hydrous high-pressure olivine holding 1.5% water by weight at 410 miles depth"
            },
            {
                "id": "cold_plasma",
                "name": "Cold Atmospheric Plasma",
                "species": "Ionized Gas",
                "traits": "Room-temperature plasma discharge with high-energy electrons but ambient heavy ions"
            },
            {
                "id": "quantum_eraser",
                "name": "Delayed-Choice Eraser",
                "species": "Quantum Optics",
                "traits": "Interferometer proving which-way knowledge destroys interference retroactively"
            },
            {
                "id": "bootes_void",
                "name": "Boötes Supervoid",
                "species": "Cosmic Structure",
                "traits": "330-million-light-year spherical void containing only 60 galaxies instead of 2,000"
            }
        ],
        "default_voice": "en-US-ChristopherNeural",
        "episodes": [
            {
                "title": "The Ocean Floating 400 Miles Under Earth",
                "hook": "Deep beneath our feet, there is an ocean holding three times more water than all surface oceans combined.",
                "act1": "Between 250 and 410 miles below the Earth's surface lies the mantle transition zone, subjected to crushing pressures of 200,000 atmospheres.",
                "act2": "Water down there doesn't exist as liquid or ice. It is trapped inside the molecular lattice of a rare blue gemstone called ringwoodite, stored as hydroxide ions under extreme temperature.",
                "act3": "If this mineral crystal ever released its trapped water to the surface, the entire planet's continents would be submerged under miles of open ocean.",
                "scenes": [
                    {
                        "text": "Deep beneath our feet, there is an ocean holding three times more water than all surface oceans combined.",
                        "visual_prompt": "Geological cross-section cutaway of planet Earth showing crust, upper mantle, mantle transition zone at 410 miles depth, glowing blue crystal layer, 9:16 vertical layout, scientific infographic style",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Water isn't liquid down there. It is trapped inside the molecular crystal lattice of ringwoodite under 200,000 atmospheres.",
                        "visual_prompt": "Molecular crystal structure diagram of hydrous ringwoodite mineral lattice showing trapped OH hydroxide ions under extreme seismic pressure, glowing cyan bonds, 9:16 vertical format",
                        "motion": "pan_left"
                    },
                    {
                        "text": "If this mantle ocean was ever pushed to the surface, every continent on Earth would be completely submerged.",
                        "visual_prompt": "Scientific summary telemetry card with Earth seismic depth gauge (410 to 660 km), 3x total surface ocean water volume calculation, 8k scientific visualization, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "scientific"
            },
            {
                "title": "The Cold Plasma Flame That Doesn't Burn",
                "hook": "Scientists have created a glowing purple jet of plasma that you can touch with your bare hands.",
                "act1": "Plasma is the fourth state of matter, usually found in lightning bolts and the surface of the sun at thousands of degrees.",
                "act2": "Cold Atmospheric Plasma is created by pulsing high-frequency electric fields through helium gas. The light electrons are accelerated to thousands of degrees, but the heavy gas atoms remain at room temperature.",
                "act3": "Because the overall temperature stays at 30 degrees Celsius, surgeons are now using cold plasma beams to sterilize infected human tissue and destroy cancer cells without burning skin.",
                "scenes": [
                    {
                        "text": "Scientists have created a glowing purple jet of plasma that you can touch with your bare hands.",
                        "visual_prompt": "Scientific physics laboratory apparatus emitting a glowing ultraviolet cold atmospheric plasma jet pen, dark clean background, 9:16 vertical layout, scientific documentary aesthetic",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "High-voltage pulses accelerate lightweight electrons to high energy while the heavy helium atoms stay at 25 degrees Celsius.",
                        "visual_prompt": "Non-thermal plasma physics schematic showing two-temperature thermodynamic equilibrium: energetic electron swarm vs room-temperature heavy ion atoms, electric field lines, 9:16 vertical format",
                        "motion": "pan_right"
                    },
                    {
                        "text": "Medical researchers now use cold plasma to sterilize wounds and destroy bacteria in seconds with zero heat damage.",
                        "visual_prompt": "Scientific summary card highlighting Cold Plasma medical applications (antimicrobial sterilization, oncology wound healing, reactive oxygen species), clean scientific typography, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "scientific"
            },
            {
                "title": "The Boötes Void: 330 Million Light-Year Abyss",
                "hook": "In 1981, astronomers pointed their telescopes toward the constellation Boötes and found the emptiest place in the universe.",
                "act1": "A spherical region of space spanning 330 million light-years across. In a volume that size, astronomers expected to find over two thousand spiral galaxies.",
                "act2": "Instead, they found barely sixty galaxies floating in total, horrifying isolation across hundreds of millions of light-years.",
                "act3": "If our Milky Way galaxy were located in the center of the Boötes Void, we wouldn't have known other galaxies existed until the invention of deep space telescopes in the 1960s.",
                "scenes": [
                    {
                        "text": "In 1981, astronomers pointed telescopes toward Boötes and found the emptiest place in the known universe.",
                        "visual_prompt": "Deep cosmos astronomical visualization of the cosmic web showing glowing galactic filaments surrounding a massive pitch-black spherical void 330 million light years across, 9:16 vertical format",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "A void spanning 330 million light-years. Instead of 2,000 galaxies, there are only sixty.",
                        "visual_prompt": "Cosmic scale comparison diagram comparing standard galactic cluster density vs the Boötes Void supervoid, astronomical scale markers in megaparsecs, 9:16 vertical layout",
                        "motion": "pan_left"
                    },
                    {
                        "text": "If Earth were inside the Boötes Void, our night sky would have been completely pitch black beyond our own galaxy.",
                        "visual_prompt": "Astronomy infographic summary card: Boötes Void diameter (330 million light years), galaxy count (60 vs 2,000 expected), cosmic void expansion dynamics, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "scientific"
            }
        ]
    },

    "ancient_mysteries": {
        "id": "ancient_mysteries",
        "title": "Ancient Tech & Engineering Marvels",
        "category": "engineering_history",
        "description": "Lost ancient engineering secrets: Roman self-healing volcanic concrete, the 2,000-year-old Antikythera mechanical computer, and ancient precision.",
        "cast": [
            {
                "id": "pozzolana",
                "name": "Pozzolanic Ash",
                "species": "Volcanic Material",
                "traits": "Reactive volcanic ash forming interlocking aluminum-tobermorite crystals in seawater"
            },
            {
                "id": "lime_clasts",
                "name": "Lime Clasts",
                "species": "Self-Healing Chemical Matrix",
                "traits": "Quicklime inclusions that dissolve during water seepage to recrystallize calcite and heal cracks"
            },
            {
                "id": "differential_gears",
                "name": "30 Bronze Gears",
                "species": "Precision Mechanics",
                "traits": "Differential gear train calculating solar, lunar, and eclipse cycles with 1-day accuracy"
            }
        ],
        "default_voice": "en-US-ChristopherNeural",
        "episodes": [
            {
                "title": "Roman Concrete: Self-Healing Over 2,000 Years",
                "hook": "Modern concrete buildings crumble after 50 years, yet Roman sea walls are still standing strong after two thousand years.",
                "act1": "For centuries, engineers believed Romans made simple mortar from volcanic ash and slaked lime.",
                "act2": "In 2023, MIT researchers discovered that Romans used hot mixing with unslaked quicklime. This left tiny white mineral pockets called lime clasts throughout the structure.",
                "act3": "Whenever water seeps through a microscopic crack, it dissolves the lime clasts into a reactive calcium solution, recrystallizing inside the fracture and literally healing the concrete from within.",
                "scenes": [
                    {
                        "text": "Modern concrete structures crumble after 50 years, yet Roman sea piers stand strong after 2,000 years in ocean water.",
                        "visual_prompt": "Cinematic historical engineering cutaway of an ancient Roman marine pier in seawater standing next to a weathered modern concrete pillar, 9:16 vertical layout, scientific documentary style",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "MIT researchers discovered Romans hot-mixed quicklime, embedding reactive calcium lime clasts inside the concrete.",
                        "visual_prompt": "Microscopic SEM electron microscope view of Roman concrete showing lime clast calcium carbonate crystal formations sealing a micro-fracture, chemical reaction arrows, 9:16 vertical format",
                        "motion": "pan_left"
                    },
                    {
                        "text": "When seawater enters a crack, it dissolves the lime and recrystallizes into calcite, self-healing the concrete forever.",
                        "visual_prompt": "Engineering summary card: Roman Pozzolanic self-healing chemistry (CaO + H2O -> Ca(OH)2 -> CaCO3), 2,000-year durability comparison chart, crisp technical typography, 9:16 vertical layout",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "historical"
            },
            {
                "title": "Antikythera: The 2,000-Year-Old Analog Computer",
                "hook": "In 1901, sponge divers pulled a corroded lump of bronze from an ancient Greek shipwreck.",
                "act1": "For decades it sat in a museum, until modern high-resolution 3D X-ray tomography revealed an impossible mechanical marvel built in 150 BC.",
                "act2": "Packing over 30 precision interlocking bronze gears, it accurately tracked planetary movements, predicted solar and lunar eclipses, and calculated the exact four-year cycle of the ancient Olympic Games.",
                "act3": "Technology this complex vanished with the fall of Greece and would not appear on Earth again for another 1,400 years.",
                "scenes": [
                    {
                        "text": "In 1901, divers pulled a corroded bronze lump from a 2,000-year-old shipwreck off the island of Antikythera.",
                        "visual_prompt": "Cinematic archaeological discovery scene: underwater ancient Greek shipwreck with diver retrieving a corroded bronze mechanical artifact from sea silt, 9:16 vertical layout",
                        "motion": "zoom_in"
                    },
                    {
                        "text": "Modern 3D X-ray scans revealed over thirty interlocking bronze precision gears and differential mechanisms inside.",
                        "visual_prompt": "Cutaway 3D technical mechanical schematic of the Antikythera Mechanism showing interlocking bronze gear trains, differential gears, and celestial dials, glowing brass on dark blueprint, 9:16 vertical",
                        "motion": "pan_right"
                    },
                    {
                        "text": "It accurately predicted eclipses and planetary positions decades ahead. Such technology would not exist again for 1,400 years.",
                        "visual_prompt": "Archaeological engineering summary card with gear ratio equations, Saros eclipse cycle calculation, and 1,400-year technology gap timeline, crisp typography, 9:16 vertical format",
                        "motion": "zoom_out"
                    }
                ],
                "music": "ambient_glow",
                "soundtrack_genre": "historical"
            }
        ]
    }
}

class UniverseManager:
    """Manages the 5 technical and scientific knowledge domains."""

    @classmethod
    def _load_state(cls) -> Dict[str, Any]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        default_state = {
            "active_universe": "system_design",
            "universe_counters": {
                "system_design": {"season": 1, "episode": 0, "history": []},
                "computer_engineering": {"season": 1, "episode": 0, "history": []},
                "study_shorts": {"season": 1, "episode": 0, "history": []},
                "science_paradoxes": {"season": 1, "episode": 0, "history": []},
                "ancient_mysteries": {"season": 1, "episode": 0, "history": []}
            }
        }
        if not STATE_FILE.exists():
            return default_state
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                active = data.get("active_universe", "system_design")
                if active not in UNIVERSES:
                    data["active_universe"] = "system_design"
                return data
        except Exception:
            return default_state

    @classmethod
    def _save_state(cls, state: Dict[str, Any]):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        tmp.replace(STATE_FILE)

    @classmethod
    def get_all_universes(cls) -> Dict[str, Any]:
        """Returns metadata for all 5 technical and scientific domains."""
        state = cls._load_state()
        result = {}
        for uid, udata in UNIVERSES.items():
            counter = state.get("universe_counters", {}).get(uid, {"season": 1, "episode": 0})
            result[uid] = {
                "id": uid,
                "title": udata["title"],
                "category": udata["category"],
                "description": udata["description"],
                "current_season": counter.get("season", 1),
                "current_episode": counter.get("episode", 0),
                "cast": udata.get("cast", []),
                "is_active": (uid == state.get("active_universe", "system_design")),
                "total_episodes_available": len(udata.get("episodes", []))
            }
        return result

    @classmethod
    def get_active_universe_info(cls) -> Dict[str, Any]:
        """Returns full data for the currently active knowledge domain."""
        state = cls._load_state()
        uid = state.get("active_universe", "system_design")
        if uid not in UNIVERSES:
            uid = "system_design"
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
        """Switches the active knowledge domain."""
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
        """Synthesizes the next episode in the selected technical domain."""
        state = cls._load_state()
        uid = universe_id or state.get("active_universe", "system_design")
        if uid not in UNIVERSES:
            uid = "system_design"

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

        ep_code = f"S{season:02d}E{current_ep:02d}"
        full_title = f"{blueprint.get('title', 'Technical Deep Dive')}"

        hook = blueprint.get("hook", "Did you know how this engineering principle works?")
        act1 = blueprint.get("act1", "")
        act2 = blueprint.get("act2", "")
        act3 = blueprint.get("act3", "")
        full_script = f"{hook} {act1} {act2} {act3}".strip()

        scenes = blueprint.get("scenes", [])
        voice = universe.get("default_voice", "en-US-ChristopherNeural")
        music = blueprint.get("music", "cyber_pulse")

        episode_payload = {
            "id": f"{uid}_{ep_code.lower()}_{current_ep:04d}",
            "universe_id": uid,
            "season": season,
            "episode": current_ep,
            "episode_code": ep_code,
            "title": full_title,
            "genre": uid,
            "hook": hook,
            "script": full_script,
            "scenes": scenes,
            "suggested_voice": voice,
            "suggested_music": music,
            "cast": universe.get("cast", []),
            "visual_style": "vector_infographic",
            "narrative_structure": {
                "act1_hook": act1,
                "act2_escalation": act2,
                "act3_payoff": act3
            },
            "duration": 15,
            "caption_style": "clean_minimal"
        }

        # Track history
        u_counter.setdefault("history", []).append({
            "code": ep_code,
            "title": full_title,
            "hook": hook
        })
        cls._save_state(state)

        return episode_payload
