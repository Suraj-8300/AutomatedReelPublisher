import os
from pathlib import Path

# Base Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "output"
CACHE_DIR = PROJECT_DIR / "cache"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Video Specs
WIDTH = 1080
HEIGHT = 1920
FPS = 30
ASPECT_RATIO = "9:16"

# Fonts
FONTS = {
    "bold": "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
    "regular": "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
    "fallback_bold": "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
    "font_name": "Liberation Sans"
}

# Edge TTS Voices
VOICES = {
    "christopher": "en-US-ChristopherNeural",   # Energetic, viral science explainer
    "guy": "en-US-GuyNeural",                   # Authoritative, serious mystery
    "jenny": "en-US-JennyNeural",               # Engaging, crisp female
    "ava": "en-US-AvaNeural",                   # Natural storyteller female
    "andrew": "en-US-AndrewNeural",             # Deep, charismatic male
}
DEFAULT_VOICE = "en-US-ChristopherNeural"

# Color Palettes for Reels
PALETTES = {
    "cyber_blue": {
        "bg_top": (10, 15, 30),
        "bg_bottom": (5, 8, 18),
        "accent": "#00F0FF",       # Neon Cyan
        "highlight": "#FFE600",    # Electric Yellow
        "badge_bg": (20, 35, 60, 200),
        "card_bg": (15, 25, 45, 220),
        "border": (0, 240, 255, 120),
    },
    "cosmic_purple": {
        "bg_top": (25, 10, 45),
        "bg_bottom": (10, 5, 22),
        "accent": "#BD00FF",       # Neon Purple
        "highlight": "#00FFA3",    # Neon Mint
        "badge_bg": (45, 20, 70, 200),
        "card_bg": (30, 15, 50, 220),
        "border": (189, 0, 255, 120),
    },
    "deep_emerald": {
        "bg_top": (8, 28, 24),
        "bg_bottom": (4, 15, 12),
        "accent": "#00FF88",       # Neon Green
        "highlight": "#FFDD00",    # Gold Yellow
        "badge_bg": (15, 50, 40, 200),
        "card_bg": (10, 35, 30, 220),
        "border": (0, 255, 136, 120),
    },
    "crimson_flame": {
        "bg_top": (38, 12, 12),
        "bg_bottom": (18, 5, 5),
        "accent": "#FF3366",       # Hot Red
        "highlight": "#FFCC00",    # Amber
        "badge_bg": (60, 20, 20, 200),
        "card_bg": (45, 15, 15, 220),
        "border": (255, 51, 102, 120),
    },
    "cozy_warm": {
        "bg_top": (42, 24, 16),
        "bg_bottom": (22, 12, 8),
        "accent": "#FFA94D",
        "highlight": "#FFE066",
        "badge_bg": (60, 35, 25, 200),
        "card_bg": (45, 25, 18, 220),
        "border": (255, 169, 77, 120),
    },
    "nature": {
        "bg_top": (16, 36, 22),
        "bg_bottom": (8, 20, 12),
        "accent": "#69DB7C",
        "highlight": "#FFD43B",
        "badge_bg": (25, 55, 35, 200),
        "card_bg": (18, 40, 26, 220),
        "border": (105, 219, 124, 120),
    }
}

# Word Count Guidelines per Duration
DURATION_TARGETS = {
    10: {"words_min": 20, "words_max": 28, "target_secs": 10},
    15: {"words_min": 32, "words_max": 42, "target_secs": 15},
    30: {"words_min": 68, "words_max": 85, "target_secs": 30},
    60: {"words_min": 140, "words_max": 175, "target_secs": 60},
}

