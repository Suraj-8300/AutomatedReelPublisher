"""
YouTube Data API v3 Pipeline Configuration.
"""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
YOUTUBE_DIR = Path(__file__).resolve().parent

def get_client_secret_file() -> Path:
    """Finds client_secret.json in youtube/ directory or root fallback."""
    local = YOUTUBE_DIR / "client_secret.json"
    if local.exists():
        return local
    root_fallback = PROJECT_ROOT / "client_secret.json"
    if root_fallback.exists():
        return root_fallback
    return local

def get_token_file() -> Path:
    """Finds youtube_token.json in youtube/ directory or root fallback."""
    local = YOUTUBE_DIR / "youtube_token.json"
    if local.exists():
        return local
    root_fallback = PROJECT_ROOT / "youtube_token.json"
    if root_fallback.exists():
        return root_fallback
    return local

CLIENT_SECRET_FILE = get_client_secret_file()
TOKEN_FILE = get_token_file()

# OAuth 2.0 Scopes required for video upload and channel inspection
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

# Redirect URI configured in Google Cloud Console
REDIRECT_PORT = 8000
REDIRECT_PATH = "/auth/youtube/callback"
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}{REDIRECT_PATH}"

# YouTube Default Settings
DEFAULT_PRIVACY_STATUS = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")
DEFAULT_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "24")  # 24 = Entertainment, 28 = Science & Tech
DEFAULT_TAGS = ["Shorts", "Viral", "Reels", "AI", "Trending", "Story"]
