"""
Platform Publishers Module for AutoReelStudio.
Contains dedicated publishers for Instagram Reels and YouTube Shorts.
"""

from .instagram.publisher import MetaGraphPublisher as InstagramPublisher
from .instagram.queue_manager import ReelQueueManager as InstagramQueueManager
from .youtube.publisher import YouTubePublisher
from .youtube.auth import YouTubeAuthenticator
from .dispatch_queue import PublishingQueueManager

__all__ = [
    "InstagramPublisher",
    "InstagramQueueManager",
    "YouTubePublisher",
    "YouTubeAuthenticator",
    "PublishingQueueManager"
]

