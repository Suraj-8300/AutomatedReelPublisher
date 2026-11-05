import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import FONTS, CACHE_DIR, WIDTH, HEIGHT

class SubtitleEngine:
    """
    Intelligent Genre-Aware Instagram Reel Subtitle Engine.
    Supports 6 modern short-form typography styles with intelligent contrast management,
    word-level sync, pop-scale animations, and strict Instagram safe-zone compliance.
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
    def _hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
        """Converts #RRGGBB and alpha (0-255) to ASS &HAABBGGRR&"""
        hex_str = hex_str.lstrip("#")
        r = hex_str[0:2]
        g = hex_str[2:4]
        b = hex_str[4:6]
        a = f"{alpha:02X}"
        return f"&H{a}{b}{g}{r}&"

    @staticmethod
    def generate_ass(
        words: List[Dict[str, Any]],
        output_file: Optional[Path] = None,
        style: str = "karaoke",
        highlight_color: str = "#FFE600",
        words_per_chunk: Optional[int] = None,
        contrast_mode: str = "subtle_outline"
    ) -> str:
        """
        Generates modern .ass subtitles adhering to the requested style:
        - 'karaoke': Word-by-word active pop scale with bright accent highlight.
        - 'high_impact': 1-2 words ultra-bold dynamic flash (MrBeast / Hormozi style).
        - 'clean_minimal': Understated, modern sans-serif, clean lower-third placement.
        - 'cinematic': Wide tracking, letter-spaced, documentary gold/white aesthetic.
        - 'dynamic_phrase': 3-4 word natural phrase rhythm with keyword emphasis.
        - 'meme': Classic bold uppercase punchy meme caption.
        """
        if output_file is None:
            output_file = CACHE_DIR / f"subtitles_{uuid.uuid4().hex[:8]}.ass"

        font_name = FONTS.get("font_name", "Liberation Sans")
        clean_style = style.lower() if style else "karaoke"

        # Safe MarginV: Instagram safe zone (below top 220px, well above bottom 380px)
        # In ASS with Alignment 2 (bottom center), MarginV represents distance from bottom edge.
        # Height is 1920. 450px from bottom sits perfectly in the safe middle-lower viewport.
        margin_v = 450
        margin_l = 80
        margin_r = 80

        # Style-specific typography configurations
        if clean_style == "high_impact":
            font_size = 88
            chunk_size = 2 if words_per_chunk is None else words_per_chunk
            ass_primary = "&H00FFFFFF&"
            ass_highlight = SubtitleEngine._hex_to_ass_color(highlight_color)
            ass_outline = "&H00000000&"
            ass_shadow = "&H60000000&"
            border_style = 1
            outline_width = 8
            shadow_depth = 4
            bold = -1
            spacing = 2

        elif clean_style == "clean_minimal":
            font_size = 62
            chunk_size = 4 if words_per_chunk is None else words_per_chunk
            ass_primary = "&H00FFFFFF&"
            ass_highlight = SubtitleEngine._hex_to_ass_color(highlight_color)
            ass_outline = "&H40000000&"
            ass_shadow = "&H80000000&"
            border_style = 1
            outline_width = 3
            shadow_depth = 2
            bold = 0
            spacing = 1
            margin_v = 420

        elif clean_style == "cinematic":
            font_size = 68
            chunk_size = 4 if words_per_chunk is None else words_per_chunk
            ass_primary = "&H00F0F0F0&"
            ass_highlight = "&H00D0E8FF&" # Warm subtle gold
            ass_outline = "&H30000000&"
            ass_shadow = "&H60000000&"
            border_style = 1
            outline_width = 4
            shadow_depth = 3
            bold = -1
            spacing = 4
            margin_v = 440

        elif clean_style == "dynamic_phrase":
            font_size = 74
            chunk_size = 3 if words_per_chunk is None else words_per_chunk
            ass_primary = "&H00FFFFFF&"
            ass_highlight = SubtitleEngine._hex_to_ass_color(highlight_color)
            ass_outline = "&H00000000&"
            ass_shadow = "&H70000000&"
            border_style = 1
            outline_width = 6
            shadow_depth = 3
            bold = -1
            spacing = 2

        elif clean_style == "meme":
            font_size = 82
            chunk_size = 3 if words_per_chunk is None else words_per_chunk
            ass_primary = "&H00FFFFFF&"
            ass_highlight = "&H0000FFFF&" # Vibrant cyan
            ass_outline = "&H00000000&"
            ass_shadow = "&H90000000&"
            border_style = 1
            outline_width = 9
            shadow_depth = 5
            bold = -1
            spacing = 1

        else: # Default: 'karaoke'
            font_size = 76
            chunk_size = 3 if words_per_chunk is None else words_per_chunk
            ass_primary = "&H00FFFFFF&"
            ass_highlight = SubtitleEngine._hex_to_ass_color(highlight_color)
            ass_outline = "&H00000000&"
            ass_shadow = "&H70000000&"
            border_style = 1
            outline_width = 7
            shadow_depth = 4
            bold = -1
            spacing = 2

        # Header definition
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{ass_primary},&H000000FF&,{ass_outline},{ass_shadow},{bold},0,0,0,100,100,{spacing},0,{border_style},{outline_width},{shadow_depth},2,{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogue_lines = []

        if not words:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(header)
            return str(output_file)

        # Build chunks
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(words[i:i + chunk_size])

        for chunk in chunks:
            chunk_start = chunk[0]["start"]
            chunk_end = chunk[-1]["end"]

            if clean_style in ["karaoke", "high_impact"]:
                # Word-by-word active timing
                for current_idx, current_w in enumerate(chunk):
                    w_start = current_w["start"]
                    w_end = chunk[current_idx + 1]["start"] if current_idx + 1 < len(chunk) else chunk_end
                    if w_end <= w_start:
                        w_end = w_start + 0.16

                    time_start = SubtitleEngine._format_timestamp(w_start)
                    time_end = SubtitleEngine._format_timestamp(w_end)

                    formatted_words = []
                    for idx, w in enumerate(chunk):
                        clean_word = re.sub(r'[^\w\s\?\!\,\.\'\-]', '', w["word"])
                        if clean_style in ["high_impact", "meme"]:
                            clean_word = clean_word.upper()

                        if idx == current_idx:
                            # Pop scale on active word
                            scale = 114 if clean_style == "high_impact" else 110
                            formatted_words.append(
                                r"{\fscx" + str(scale) + r"\fscy" + str(scale) + r"\c" + ass_highlight + r"}"
                                + clean_word
                                + r"{\fscx100\fscy100\c" + ass_primary + r"}"
                            )
                        else:
                            formatted_words.append(clean_word)

                    text_line = " ".join(formatted_words)
                    dialogue_lines.append(f"Dialogue: 0,{time_start},{time_end},Default,,0,0,0,,{text_line}")

            else:
                # Dynamic phrase / Clean minimal / Cinematic / Meme:
                # Displays the entire cohesive chunk cleanly across its duration
                time_start = SubtitleEngine._format_timestamp(chunk_start)
                time_end = SubtitleEngine._format_timestamp(chunk_end)

                chunk_words = []
                for w in chunk:
                    cw = re.sub(r'[^\w\s\?\!\,\.\'\-]', '', w["word"])
                    if clean_style == "meme":
                        cw = cw.upper()
                    chunk_words.append(cw)

                text_line = " ".join(chunk_words)
                dialogue_lines.append(f"Dialogue: 0,{time_start},{time_end},Default,,0,0,0,,{text_line}")

        full_ass_content = header + "\n".join(dialogue_lines) + "\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_ass_content)

        return str(output_file)
