"""
Natural Neural Voice & Speech Synthesis Engine for AutoReelStudio.
Uses Microsoft Edge Neural TTS models to produce high-fidelity human speech
with sub-word timestamp extraction for synchronized dynamic subtitles.
"""

import os
import sys
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Edge TTS High-Fidelity Voices
RECOMMENDED_VOICES = {
    "energetic": "en-US-ChristopherNeural",
    "deep_mystery": "en-US-GuyNeural",
    "conversational_female": "en-US-JennyNeural",
    "charismatic_male": "en-US-AndrewNeural",
    "storyteller": "en-US-AvaNeural"
}

class NaturalVoiceEngine:
    """Synthesizes human-like narration and extracts word-level timing markers."""

    @classmethod
    async def synthesize_speech(
        cls,
        text: str,
        voice: str = "en-US-ChristopherNeural",
        rate: str = "+4%",
        pitch: str = "+0Hz"
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """
        Synthesizes text into high-fidelity MP3 audio and maps word-level timestamps.
        Returns: (audio_path, word_timings, total_duration)
        """
        try:
            import edge_tts
        except ImportError:
            # Fallback path if bundled wheel/lib is in lib/
            lib_path = Path(__file__).resolve().parent.parent / "lib"
            if str(lib_path) not in sys.path:
                sys.path.insert(0, str(lib_path))
            import edge_tts

        text_hash = hashlib.md5(f"{text}_{voice}_{rate}".encode()).hexdigest()[:12]
        audio_file = CACHE_DIR / f"voice_{text_hash}.mp3"

        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        submaker = edge_tts.SubMaker()

        # Stream and capture word offsets
        with open(audio_file, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        # Extract structured word-level timings
        words_timing = []
        for offset, text_word in submaker.offset:
            start_sec = offset[0].total_seconds()
            end_sec = offset[1].total_seconds()
            words_timing.append({
                "word": text_word,
                "start": start_sec,
                "end": end_sec,
                "duration": end_sec - start_sec
            })

        total_duration = words_timing[-1]["end"] if words_timing else 15.0

        return audio_file, words_timing, total_duration

