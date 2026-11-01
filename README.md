# ⚡ ReelPublisher — Autonomous AI Video Generator & Meta Reels Publisher

> **100% Free & Open-Source Autonomous Video Studio and Direct Meta Graph API Publisher for Instagram Reels (1080x1920 9:16). Runs purely on local hardware or within cloud containers.**

[![GitHub](https://img.shields.io/badge/GitHub-Suraj--8300%2FAutomatedReelPublisher-blue?logo=github)](https://github.com/Suraj-8300/AutomatedReelPublisher)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://python.org)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-6.0%2B-green.svg)](https://ffmpeg.org)
[![Meta Graph API](https://img.shields.io/badge/Meta%20Graph%20API-v21.0-4267B2?logo=facebook)](https://developers.facebook.com)
[![Instagram](https://img.shields.io/badge/Instagram%20Reels-@sun__27417-E4405F?logo=instagram)](https://instagram.com)

---

## 🌟 Architecture & Features

ReelPublisher provides a complete web studio and automated backend for end-to-end social media publishing:

1. **⚡ 1-Click Generate & Publish**: Refines an idea, synthesizes neural voiceover (Edge-TTS), fetches matching contextual B-roll footage, renders word-by-word highlighted subtitles, normalizes to Meta's strict 1080x1920 technical specs, exposes the video over an encrypted Zero-Card TLS Bridge, and publishes it live to Instagram Reels via the official Meta Graph API.
2. **🎬 Draft Generation & Inspector**: Generate videos as drafts first to inspect them, test safe-zone danger overlays (Meta top 220px / bottom 380px UI boundaries), and audit technical compliance before publishing.
3. **📲 Granular Publishing Actions**: Publish any draft directly from the interactive preview player or library gallery with real-time status and live Instagram permalink receipts (`https://www.instagram.com/reel/...`).
4. **🌐 Zero-Card Public TLS Bridge**: Eliminates external paid storage or credit cards by establishing an on-demand, encrypted reverse TLS tunnel (`*.lhr.life` via OpenSSH) directly to Meta's ingestion servers.
5. **🐳 Container & Cloudflare Portfolio Ready**: Packaged with a production-grade `Dockerfile` for Hugging Face Spaces / Docker containers and integrated into the `00ProjectSun` personal portfolio website.

---

## 🖥️ Web Studio Interface

Launch the local web studio with one command:

```bash
python3 server.py
# or: python3 web_ui.py
```
Open **`http://localhost:8080`** in your browser to access:
- **Hero 1-Click Generate & Publish Button**: Autonomous end-to-end creation and upload.
- **Draft Generator**: Video preview without immediate upload.
- **Safe-Zone Overlay**: Real-time visualization of Meta's header and caption safe areas.
- **Spec Inspector**: Probes resolution, aspect ratio, frame rate, audio sample rate, and faststart moov atom status.
- **Archive Gallery**: Browse past generated videos, inspect specs, and publish with 1 click.

---

## 🛠️ CLI Tools

You can also run every pipeline stage directly from your terminal:

```bash
# 1. Audit any video against Instagram Reels technical specs
python3 reel_publisher.py check output/my_video.mp4

# 2. Normalize video to 1080x1920 H.264/AAC with faststart
python3 reel_publisher.py normalize input.mp4 --mode pad

# 3. Render safe-zone danger overlay debug frame
python3 reel_publisher.py preview input.mp4

# 4. Process and publish a single video file live
python3 reel_publisher.py process output/my_video.mp4

# 5. Continuous inbox watcher daemon
python3 reel_publisher.py watch
```

---

## ⚙️ Configuration (`.env`)

ReelPublisher reads credentials and pipeline configurations from `.env`:

```ini
# Meta Graph API Configuration
META_GRAPH_API_VERSION=v21.0
INSTAGRAM_ACCOUNT_ID=17841476861770479
META_ACCESS_TOKEN="YOUR_META_LONG_LIVED_TOKEN"

# Cloud Bridge: "tunnel" (100% Free Zero-Card TLS Bridge) or "r2" / "s3"
STORAGE_PROVIDER=tunnel
AUTO_DELETE_CLOUD_OBJECT=true

# Video Transcoding Options
DEFAULT_SCALING_MODE=pad
VIDEO_TARGET_BITRATE=4.5M
VIDEO_MAX_BITRATE=5.0M
AUDIO_SAMPLE_RATE=48000
AUDIO_CHANNELS=2
```

---

## 🐳 Docker / Hugging Face Spaces Container

Build and run in a container environment:

```bash
# Build Docker image
docker build -t reelpublisher .

# Run container on port 7860
docker run -p 7860:7860 --env-file .env reelpublisher
```

---

## 📄 License
MIT License. Created by Suraj D (@Suraj-8300).
