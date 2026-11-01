import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import FONTS, CACHE_DIR, WIDTH, HEIGHT

class SubtitleEngine:
    """
    Upgraded Viral TikTok / Instagram Reel subtitle generator.
    Produces high-retention karaoke style word-by-word highlighted captions
    with pop-scale animations and strict safe-zone alignment.
    """

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Converts seconds into ASS timestamp: H:MM:SS.cs"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        cs = int(round((seconds - int(seconds)) * 100))
        if cs >= 100:
            secs += 1
            cs = 0
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

    @staticmethod
    def _hex_to_ass_color(hex_str: str) -> str:
        """Converts #RRGGBB to ASS &H00BBGGRR&"""
        hex_str = hex_str.lstrip("#")
        r = hex_str[0:2]
        g = hex_str[2:4]
        b = hex_str[4:6]
        return f"&H00{b}{g}{r}&"

    @staticmethod
    def generate_ass(
        words: List[Dict[str, Any]],
        output_file: Optional[Path] = None,
        highlight_color: str = "#FFE600",
        words_per_chunk: int = 3
    ) -> str:
        if output_file is None:
            output_file = CACHE_DIR / f"subtitles_{uuid.uuid4().hex[:8]}.ass"

        font_name = FONTS.get("font_name", "Liberation Sans")
        ass_highlight = SubtitleEngine._hex_to_ass_color(highlight_color)
        ass_white = "&H00FFFFFF&"
        ass_outline = "&H00000000&"
        ass_shadow = "&H80000000&"

        # ASS Script Header with viral TikTok typography
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},78,{ass_white},&H000000FF&,{ass_outline},{ass_shadow},-1,0,0,0,100,100,2,0,1,8,4,2,70,140,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogue_lines = []

        if not words:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(header)
            return str(output_file)

        # Group words into 2-3 word chunks (high eye-tracking retention)
        chunks = []
        for i in range(0, len(words), words_per_chunk):
            chunks.append(words[i:i + words_per_chunk])

        for chunk in chunks:
            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"]

            for current_idx, current_w in enumerate(chunk):
                w_start = current_w["start"]
                w_end = chunk[current_idx + 1]["start"] if current_idx + 1 < len(chunk) else chunk_end

                if w_end <= w_start:
                    w_end = w_start + 0.16

                time_start = SubtitleEngine._format_timestamp(w_start)
                time_end = SubtitleEngine._format_timestamp(w_end)

                formatted_words = []
                for idx, w in enumerate(chunk):
                    clean_word = re.sub(r'[^\w\s\?\!\,\.\'\-]', '', w["word"]).upper()
                    if idx == current_idx:
                        # Animated Pop Scale on active word
                        formatted_words.append(r"{\fscx112\fscy112\c" + ass_highlight + r"}" + clean_word + r"{\fscx100\fscy100\c" + ass_white + r"}")
                    else:
                        formatted_words.append(clean_word)

                text_line = " ".join(formatted_words)
                dialogue_lines.append(f"Dialogue: 0,{time_start},{time_end},Default,,0,0,0,,{text_line}")

        full_ass_content = header + "\n".join(dialogue_lines) + "\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_ass_content)

        return str(output_file)
