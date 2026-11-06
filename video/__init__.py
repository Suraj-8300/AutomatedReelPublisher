"""
AutoReelStudio Video Module.

Publishing utilities:
  CDNOptimizer       — Faststart moov-atom, 1080x1920 conformance
  MetadataPackager   — Platform captions, hashtags, YouTube #Shorts titles

Generation engine:
  ReelGenerator      — Generate a single reel (any pillar)
  BatchGenerator     — Generate a full day's batch of reels
"""

from .cdn_optimizer import CDNOptimizer
from .metadata_packager import MetadataPackager
from .generator import ReelGenerator, BatchGenerator

__all__ = [
    "CDNOptimizer",
    "MetadataPackager",
    "ReelGenerator",
    "BatchGenerator",
]
