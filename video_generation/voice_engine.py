"""
Natural Neural Voice & Speech Synthesis Engine for AutoReelStudio.
Uses high-fidelity Microsoft Neural Speech models (Andrew, Christopher, Brian, Ava)
with word-level millisecond timestamp extraction for synchronized dynamic typography.
Zero robotic artifacts, 100% free with zero API keys.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.tts_engine import TTSEngine

# Industry-Grade Viral Documentary & Storytelling Neural Voices
RECOMMENDED_VOICES = {
    "documentary": "en-US-AndrewMultilingualNeural",       # Deep, magnetic documentary tone (top retention)
    "energetic": "en-US-ChristopherNeural",               # Authoritative, high energy, captivating
    "british_narrator": "en-US-BrianMultilingualNeural",   # Crisp, intellectual BBC-style narrator
    "female_storyteller": "en-US-AvaMultilingualNeural",   # Warm, expressive, highly natural female voice
    "dark_mystery": "en-US-GuyNeural"                     # Serious, intriguing, atmospheric
}

DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"

class NaturalVoiceEngine:
    """Synthesizes human-like storytelling narration and extracts word-level timing markers."""

    @classmethod
    async def synthesize_speech(
        cls,
        text: str,
        voice: str = DEFAULT_VOICE,
        rate: str = "+3%",
        pitch: str = "+0Hz"
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """
        Synthesizes text into high-fidelity MP3 audio and maps word-level timestamps.
        Returns: (audio_path, word_timings, total_duration)
        """
        # Map voice aliases or defaults
        target_voice = RECOMMENDED_VOICES.get(voice, voice)
        if not target_voice or target_voice == "AUTO":
            target_voice = DEFAULT_VOICE

        result = await TTSEngine.synthesize(
            text=text,
            voice=target_voice,
            rate=rate,
            pitch=pitch
        )

        audio_path = Path(result["audio_file"])
        words_timing = result.get("words", [])
        total_duration = result.get("duration", 15.0)

        return audio_path, words_timing, total_duration
