"""
Central configuration for AutoReelStudio video generation pipeline.
All settings are read from environment variables with sensible defaults.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = Path(__file__).resolve().parent
CACHE_DIR = VIDEO_DIR / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _load_dotenv():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k and k not in os.environ:
                os.environ[k] = v

_load_dotenv()

# --- Gemini / AI Brain ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("AI_STUDIO_KEY") or ""
GEMINI_SCRIPT_MODEL = os.getenv("GEMINI_SCRIPT_MODEL", "gemini-3.5-flash")

# --- Edge-TTS Voice Engine ---
VOICE_PROFILES = {
    "documentary":      "en-US-AndrewMultilingualNeural",
    "energetic":        "en-US-ChristopherNeural",
    "british":          "en-US-BrianMultilingualNeural",
    "female":           "en-US-AvaMultilingualNeural",
    "storyteller":      "en-US-AndrewMultilingualNeural",
    "warm_story":       "en-US-AvaMultilingualNeural",
    "dark_mystery":     "en-US-GuyNeural",
}
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "female")

# --- Pillar → Voice + Music mapping ---
PILLAR_VOICE = {
    "animal_story":  "female",
    "storytelling":  "female",
    "cute_animals":  "female",
    "ugc_lifestyle": "female",
    "ugc_ad":        "female",
    "cinematic":     "dark_mystery",
    "science":       "documentary",
    "mechanical":    "british",
    "explainer":     "documentary",
}
PILLAR_MUSIC = {
    "animal_story":  "heartwarming_story",
    "storytelling":  "heartwarming_story",
    "cute_animals":  "heartwarming_story",
    "ugc_lifestyle": "upbeat_summer",
    "ugc_ad":        "upbeat_summer",
    "cinematic":     "deep_mystery",
    "science":       "ambient_glow",
    "mechanical":    "cyber_pulse",
    "explainer":     "curiosity_lofi",
}

# --- Pollinations.ai Image Config ---
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "flux")     # "flux" is free, high quality

# --- Video Render Config ---
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
VIDEO_CRF = int(os.getenv("VIDEO_CRF", "22"))       # Lower = higher quality
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "fast")

# --- Daily Quota ---
MAX_REELS_PER_DAY = int(os.getenv("MAX_REELS_PER_DAY", "50"))
