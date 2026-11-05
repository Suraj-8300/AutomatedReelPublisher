"""
YouTube Data API v3 Pipeline Configuration.
"""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLIENT_SECRET_FILE = PROJECT_ROOT / "client_secret.json"
TOKEN_FILE = PROJECT_ROOT / "youtube_token.json"

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
