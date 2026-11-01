FROM python:3.12-slim

# System environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOME=/home/user

# Create unprivileged user 1000 for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user
WORKDIR $HOME/app

# Install system dependencies: FFmpeg, TrueType fonts, and OpenSSH for Zero-Card TLS Bridge
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-liberation \
    fonts-dejavu-core \
    openssh-client \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=user:user . .

# Ensure working queue directories exist with correct permissions
RUN mkdir -p cache output reels_inbox reels_processing reels_archive reels_failed \
    && chown -R user:user $HOME/app

# Switch to non-root user
USER user

# Expose default container port
EXPOSE 7860

# Run ReelPublisher Server
CMD ["python3", "server.py"]

