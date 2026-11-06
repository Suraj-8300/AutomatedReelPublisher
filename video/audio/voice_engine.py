"""
Neural Voice Engine using Microsoft Edge-TTS (100% free, unlimited).
Generates studio-quality narration with millisecond word-level timestamps
for synchronized dynamic subtitle rendering.
"""

import asyncio
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from video.config import CACHE_DIR, VOICE_PROFILES, DEFAULT_VOICE

_AUDIO_CACHE = CACHE_DIR / "audio"
_AUDIO_CACHE.mkdir(parents=True, exist_ok=True)

try:
    import edge_tts
    _EDGE_TTS_AVAILABLE = True
except ImportError:
    _EDGE_TTS_AVAILABLE = False


class VoiceEngine:
    """
    Synthesizes narration audio using Microsoft's Neural TTS voices (Edge-TTS).
    Extracts word-level timestamps for karaoke subtitle synchronization.
    """

    @classmethod
    async def synthesize(
        cls,
        text: str,
        voice_style: str = DEFAULT_VOICE,
        rate: str = "+5%",
        pitch: str = "+0Hz",
        output_path: Optional[Path] = None,
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """
        Synthesizes text to MP3 audio with word-level timing data.

        Returns:
            (audio_path, word_timings, total_duration_seconds)
            word_timings: list of {word, start_ms, end_ms, duration_ms}
        """
        if not _EDGE_TTS_AVAILABLE:
            raise ImportError(
                "edge-tts not installed. Run: pip install edge-tts"
            )

        # Resolve voice name
        voice_name = VOICE_PROFILES.get(voice_style, VOICE_PROFILES.get(DEFAULT_VOICE))
        if not voice_name:
            voice_name = "en-US-AndrewMultilingualNeural"

        if output_path is None:
            uid = uuid.uuid4().hex[:8]
            output_path = _AUDIO_CACHE / f"voice_{uid}.mp3"

        communicate = edge_tts.Communicate(text=text, voice=voice_name, rate=rate, pitch=pitch)

        word_timings = []
        audio_data = bytearray()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    "word": chunk.get("text", ""),
                    "start_ms": chunk.get("offset", 0) // 10000,   # 100ns → ms
                    "end_ms": (chunk.get("offset", 0) + chunk.get("duration", 0)) // 10000,
                    "duration_ms": chunk.get("duration", 0) // 10000,
                })
            elif chunk["type"] == "SentenceBoundary":
                words = chunk.get("text", "").split()
                sent_start = chunk.get("offset", 0) // 10000
                sent_dur = chunk.get("duration", 0) // 10000
                if words and sent_dur > 0:
                    per_word = sent_dur / len(words)
                    for idx, w in enumerate(words):
                        w_start = int(sent_start + idx * per_word)
                        w_end = int(sent_start + (idx + 1) * per_word)
                        word_timings.append({
                            "word": w,
                            "start_ms": w_start,
                            "end_ms": w_end,
                            "duration_ms": int(per_word),
                        })

        # Write MP3 audio
        with open(output_path, "wb") as f:
            f.write(audio_data)

        # Estimate total duration from word timings or file
        if word_timings:
            total_ms = max(w["end_ms"] for w in word_timings)
            total_duration = total_ms / 1000.0 + 1.0  # +1s buffer
        else:
            total_duration = cls._estimate_duration(text)

        return output_path, word_timings, total_duration

    @classmethod
    def synthesize_sync(
        cls,
        text: str,
        voice_style: str = DEFAULT_VOICE,
        rate: str = "+5%",
        pitch: str = "+0Hz",
        output_path: Optional[Path] = None,
    ) -> Tuple[Path, List[Dict[str, Any]], float]:
        """Synchronous wrapper around the async synthesize method."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        cls.synthesize(text, voice_style, rate, pitch, output_path)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    cls.synthesize(text, voice_style, rate, pitch, output_path)
                )
        except RuntimeError:
            return asyncio.run(
                cls.synthesize(text, voice_style, rate, pitch, output_path)
            )

    @staticmethod
    def _estimate_duration(text: str) -> float:
        """Rough estimate: ~150 words/min speaking rate."""
        words = len(text.split())
        return max(10.0, words / 2.5)   # ~150 wpm = 2.5 words/sec
