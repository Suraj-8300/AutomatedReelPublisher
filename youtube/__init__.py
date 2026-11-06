"""
YouTube Shorts Video Publishing & OAuth Module.
"""

from .auth import YouTubeAuthenticator
from .publisher import YouTubePublisher
from .config import (
    CLIENT_SECRET_FILE,
    TOKEN_FILE,
    DEFAULT_PRIVACY_STATUS,
    DEFAULT_CATEGORY_ID,
    DEFAULT_TAGS
)

__all__ = [
    "YouTubeAuthenticator",
    "YouTubePublisher",
    "CLIENT_SECRET_FILE",
    "TOKEN_FILE",
    "DEFAULT_PRIVACY_STATUS",
    "DEFAULT_CATEGORY_ID",
    "DEFAULT_TAGS"
]
