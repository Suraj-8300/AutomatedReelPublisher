"""
FFmpeg Composition Engine for AutoReelStudio.
Assembles the final 1080x1920 9:16 MP4 from visual clips, audio, and subtitles.
"""
from .ken_burns import KenBurnsEngine
from .subtitle_engine import SubtitleEngine
from .compositor import Compositor

__all__ = ["KenBurnsEngine", "SubtitleEngine", "Compositor"]
