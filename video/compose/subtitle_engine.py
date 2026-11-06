"""
Dynamic Pop Subtitle Engine for AutoReelStudio.
Generates word-by-word synchronized ASS karaoke subtitles positioned
in the vertical safe zone (above Instagram/YouTube UI buttons).
Supports karaoke, high-impact, and cinematic subtitle styles.
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from video.config import CACHE_DIR

_SUB_CACHE = CACHE_DIR / "subtitles"
_SUB_CACHE.mkdir(parents=True, exist_ok=True)

# ASS timestamp format: H:MM:SS.cs (centiseconds)
def _ms_to_ass(ms: int) -> str:
    cs = ms // 10
    s = cs // 100
    cs = cs % 100
    m = s // 60
    s = s % 60
    h = m // 60
    m = m % 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# ASS style definitions — MarginV=480 keeps text above IG/YT overlay UI
ASS_STYLES = {
    "karaoke": (
        "Style: Karaoke,Arial,96,&H00FFFFFF,&H0000FFFF,&H00000000,&HB0000000,"
        "-1,0,0,0,100,100,0,0,1,6.5,3.5,2,40,40,480,1"
    ),
    "high_impact": (
        "Style: HighImpact,Impact,106,&H0000F5FF,&H00000000,&H00000000,&HB0000000,"
        "-1,0,0,0,105,100,1,0,1,7.5,4.0,2,30,30,480,1"
    ),
    "cinematic": (
        "Style: Cinematic,Georgia,94,&H00F0F4FC,&H00000000,&H00000000,&H90000000,"
        "-1,0,0,0,100,100,1,0,1,6.0,3.0,2,40,40,480,1"
    ),
    "clean": (
        "Style: Clean,Helvetica,88,&H00FFFFFF,&H00000000,&H00000000,&H80000000,"
        "-1,0,0,0,100,100,0,0,1,5.5,2.5,2,40,40,480,1"
    ),
}

# Pillar → subtitle style mapping
PILLAR_SUBTITLE_STYLE = {
    "cinematic":  "cinematic",
    "science":    "karaoke",
    "mechanical": "high_impact",
    "explainer":  "clean",
}


class SubtitleEngine:
    """
    Generates ASS subtitle files with word-by-word active pop highlighting.
    Words are grouped into short 3–5 word display chunks for maximum readability
    on mobile screens — matching the viral CapCut/Hormozi subtitle style.
    """

    WORDS_PER_CHUNK = 4   # How many words to show at once

    @classmethod
    def generate(
        cls,
        word_timings: List[Dict[str, Any]],
        style: str = "karaoke",
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generates an ASS subtitle file from word-level timestamps.

        Args:
            word_timings: List of {word, start_ms, end_ms} dicts from VoiceEngine
            style: Subtitle style key (karaoke/high_impact/cinematic/clean)
            output_path: Where to save the .ass file

        Returns:
            Path to the generated .ass file
        """
        if output_path is None:
            cache_key = hashlib.md5(
                f"{len(word_timings)}_{style}_{word_timings[0]['word'] if word_timings else ''}".encode()
            ).hexdigest()[:10]
            output_path = _SUB_CACHE / f"subs_{cache_key}.ass"

        if output_path.exists():
            return output_path

        style_def = ASS_STYLES.get(style, ASS_STYLES["karaoke"])
        style_name = style_def.split(",")[0].replace("Style: ", "")

        events = cls._build_events(word_timings, style_name)

        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_def}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{events}"""

        output_path.write_text(ass_content, encoding="utf-8")
        return output_path

    @classmethod
    def _build_events(cls, word_timings: List[Dict], style_name: str) -> str:
        """Groups words into display chunks and generates ASS Dialogue lines."""
        if not word_timings:
            return ""

        lines = []
        # Group into chunks of WORDS_PER_CHUNK
        chunks = [
            word_timings[i : i + cls.WORDS_PER_CHUNK]
            for i in range(0, len(word_timings), cls.WORDS_PER_CHUNK)
        ]

        for chunk in chunks:
            if not chunk:
                continue
            start_ms = chunk[0]["start_ms"]
            end_ms = chunk[-1]["end_ms"]

            # Build karaoke-style text: each word highlighted as it's spoken
            text_parts = []
            for w in chunk:
                word_dur_cs = max(1, (w["end_ms"] - w["start_ms"]) // 10)
                # {\\kf<cs>} = karaoke fill highlight over word_dur centiseconds
                text_parts.append(f"{{\\kf{word_dur_cs}}}{w['word']}")
            text = " ".join(text_parts)

            start_ass = _ms_to_ass(start_ms)
            end_ass = _ms_to_ass(end_ms + 100)   # slight buffer

            lines.append(
                f"Dialogue: 0,{start_ass},{end_ass},{style_name},,0,0,0,,{text}"
            )

        return "\n".join(lines)

    @classmethod
    def generate_simple(
        cls,
        text: str,
        total_duration: float,
        style: str = "karaoke",
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Fallback: generates evenly-spaced subtitles when word timestamps
        are unavailable. Splits text into chunks and spaces them evenly.
        """
        words = text.split()
        total_ms = int(total_duration * 1000)
        ms_per_word = total_ms // max(len(words), 1)

        word_timings = []
        for i, word in enumerate(words):
            word_timings.append({
                "word": word,
                "start_ms": i * ms_per_word,
                "end_ms": (i + 1) * ms_per_word,
            })

        return cls.generate(word_timings, style=style, output_path=output_path)
