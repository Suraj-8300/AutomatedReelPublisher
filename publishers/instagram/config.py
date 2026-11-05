import os
from pathlib import Path
from typing import Optional

# Base Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_dotenv(env_path: Optional[Path] = None):
    """Simple, dependency-free .env loader that populates os.environ."""
    target = env_path or (PROJECT_ROOT / ".env")
    if not target.exists():
        return
    try:
        with open(target, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

# Automatically load .env if present
load_dotenv()

# Queue Directories
INBOX_DIR = Path(os.getenv("REELS_INBOX_DIR", PROJECT_ROOT / "reels_inbox")).resolve()
PROCESSING_DIR = Path(os.getenv("REELS_PROCESSING_DIR", PROJECT_ROOT / "reels_processing")).resolve()
ARCHIVE_DIR = Path(os.getenv("REELS_ARCHIVE_DIR", PROJECT_ROOT / "reels_archive")).resolve()
FAILED_DIR = Path(os.getenv("REELS_FAILED_DIR", PROJECT_ROOT / "reels_failed")).resolve()

for directory in [INBOX_DIR, PROCESSING_DIR, ARCHIVE_DIR, FAILED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Meta Graph API Settings
META_GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v21.0")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_API_BASE_URL = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"
META_API_TIMEOUT = int(os.getenv("META_API_TIMEOUT", "60"))
CONTAINER_POLL_INTERVAL = int(os.getenv("CONTAINER_POLL_INTERVAL", "5"))
CONTAINER_POLL_TIMEOUT = int(os.getenv("CONTAINER_POLL_TIMEOUT", "300"))

# Cloud Storage Bridge Settings (AWS S3 / Cloudflare R2 / MinIO / Local)
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "s3").lower()  # "s3", "r2", "minio", "local"
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", None)  # e.g. https://<id>.r2.cloudflarestorage.com
S3_REGION_NAME = os.getenv("S3_REGION_NAME", "auto")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
S3_PUBLIC_URL_PREFIX = os.getenv("S3_PUBLIC_URL_PREFIX", "")  # e.g. https://pub-xxx.r2.dev or CDN domain
S3_PRESIGNED_TTL = int(os.getenv("S3_PRESIGNED_TTL", "7200"))  # 2 hours
AUTO_DELETE_CLOUD_OBJECT = os.getenv("AUTO_DELETE_CLOUD_OBJECT", "true").lower() in ("true", "1", "yes")

# Instagram Reels Technical Specifications
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
VIDEO_CODEC = "h264"
AUDIO_CODEC = "aac"
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2
AUDIO_BITRATE = "192k"
VIDEO_TARGET_BITRATE = "4500k"
VIDEO_MAX_BITRATE = "5000k"
VIDEO_BUF_SIZE = "9000k"

# Validation Thresholds
MIN_DURATION_SECS = 3.0
MAX_DURATION_SECS = 90.0
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024  # 1 GB
TARGET_FILE_SIZE_WARNING_BYTES = 100 * 1024 * 1024  # 100 MB

# Safe Zone Specifications (Instagram Mobile App Overlays)
# Top 220px: Account header, search bar, status bar
# Bottom 380px: Audio track ticker, caption text, account tag, engagement icons
SAFE_ZONE_TOP = 220
SAFE_ZONE_BOTTOM = 380
SAFE_ZONE_HEIGHT = TARGET_HEIGHT - SAFE_ZONE_TOP - SAFE_ZONE_BOTTOM  # 1320px
SAFE_ZONE_LEFT = 60
SAFE_ZONE_RIGHT = 60
SAFE_ZONE_WIDTH = TARGET_WIDTH - SAFE_ZONE_LEFT - SAFE_ZONE_RIGHT  # 960px

# Scaling Modes: "pad" (fit + black letterbox), "crop" (center crop to 9:16), "blur_pad" (blurred bg)
DEFAULT_SCALING_MODE = os.getenv("SCALING_MODE", "pad")

