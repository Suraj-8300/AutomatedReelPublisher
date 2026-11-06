"""
Dynamic Subtitle & Typography Engine for AutoReelStudio.
Generates advanced ASS subtitles with word-by-word active pop, karaoke highlights,
and strict safe-zone compliance (avoids bottom 420px Instagram/Shorts overlays).
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Any

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class SubtitleEngine:
    """Generates styled ASS subtitle tracks positioned in the vertical safe zone."""

    @classmethod
    def generate_ass(
        cls,
        words_timing: List[Dict[str, Any]],
        style: str = "karaoke"
    ) -> Path:
        """
        Builds a styled ASS subtitle file from mapped word timestamps.
        """
        ass_hash = hashlib.md5(f"{len(words_timing)}_{style}_{words_timing[0]['word'] if words_timing else ''}".encode()).hexdigest()[:8]
        out_ass = CACHE_DIR / f"subs_{style}_{ass_hash}.ass"

        # Style definitions (MarginV=480 ensures safe-zone compliance above UI buttons, large bold font)
        styles_map = {
            "karaoke": (
                "Style: Karaoke,Arial,96,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,"
                "-1,0,0,0,100,100,0,0,1,6.5,3.5,2,40,40,480,1"
            ),
            "high_impact": (
                "Style: HighImpact,Impact,106,&H0000F5FF,&H00000000,&H00000000,&H90000000,"
                "-1,0,0,0,105,100,1,0,1,7.5,4.0,2,30,30,480,1"
            ),
            "clean_minimal": (
                "Style: CleanMinimal,Helvetica,92,&H00FFFFFF,&H00000000,&H00000000,&H80000000,"
                "-1,0,0,0,100,100,0,0,1,5.5,2.5,2,40,40,480,1"
            ),
            "cinematic": (
                "Style: Cinematic,Georgia,94,&H00F0F4FC,&H00000000,&H00000000,&H80000000,"
                "-1,0,0,0,100,100,1,0,1,6.0,3.0,2,40,40,480,1"
            )
        }
        chosen_style = styles_map.get(style, styles_map["karaoke"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{chosen_style}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        if style == "karaoke":
            # Group words into 2-3 word phrases with active word highlighting for high legibility
            chunk_size = 3
            for i in range(0, len(words_timing), chunk_size):
                chunk = words_timing[i:i + chunk_size]
                if not chunk:
                    continue
                start_time = cls._format_ts(chunk[0]["start"])
                end_time = cls._format_ts(chunk[-1]["end"])

                # Karaoke timing formatting: {\k<cs>} per word
                karaoke_text = ""
                for w in chunk:
                    duration_cs = max(10, int(w["duration"] * 100))
                    karaoke_text += f"{{\\k{duration_cs}}}{w['word']} "

                events.append(f"Dialogue: 0,{start_time},{end_time},Karaoke,,0,0,0,,{karaoke_text.strip()}")
        else:
            # Phrase-level display (2-3 words per chunk)
            chunk_size = 3
            for i in range(0, len(words_timing), chunk_size):
                chunk = words_timing[i:i + chunk_size]
                if not chunk:
                    continue
                start_time = cls._format_ts(chunk[0]["start"])
                end_time = cls._format_ts(chunk[-1]["end"])
                phrase = " ".join([w["word"] for w in chunk])
                events.append(f"Dialogue: 0,{start_time},{end_time},{style.capitalize()},,0,0,0,,{phrase}")

        content = header + "\n".join(events) + "\n"
        with open(out_ass, "w", encoding="utf-8") as f:
            f.write(content)

        return out_ass

    @staticmethod
    def _format_ts(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

