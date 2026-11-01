import os
import time
import uuid
import re
import socket
import mimetypes
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .config import (
    STORAGE_PROVIDER,
    S3_BUCKET_NAME,
    S3_ENDPOINT_URL,
    S3_REGION_NAME,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_PUBLIC_URL_PREFIX,
    S3_PRESIGNED_TTL,
    AUTO_DELETE_CLOUD_OBJECT
)

class TunnelMediaHandler(BaseHTTPRequestHandler):
    """Serves media files to Meta's ingestion service with range & streaming support."""
    def log_message(self, format, *args):
        pass # Silence logging to keep CLI clean

    def do_GET(self):
        filename = self.path.lstrip("/").split("?")[0]
        file_path = ZeroCardTunnelBridge._file_mapping.get(filename)
        if file_path and Path(file_path).exists():
            p = Path(file_path)
            content_type = "video/mp4" if p.suffix.lower() == ".mp4" else "image/jpeg"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(p.stat().st_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            try:
                with open(p, "rb") as f:
                    while chunk := f.read(64 * 1024):
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_error(404, "File not found")

class ZeroCardTunnelBridge:
    """
    100% Free, Zero-Card, Zero-Setup Public HTTPS Tunnel for Meta Graph API Ingestion.
    Uses OpenSSH TLS tunneling via localhost.run to securely expose local video files
    directly to Meta's servers without requiring third-party cloud storage accounts.
    """
    _server: Optional[HTTPServer] = None
    _proc: Optional[subprocess.Popen] = None
    _public_domain: Optional[str] = None
    _port: int = 0
    _file_mapping: Dict[str, str] = {}
    _lock = threading.Lock()

    @classmethod
    def start_if_needed(cls):
        with cls._lock:
            if cls._proc and cls._public_domain:
                return

            # 1. Bind local free port
            s = socket.socket()
            s.bind(('127.0.0.1', 0))
            cls._port = s.getsockname()[1]
            s.close()

            # 2. Start local HTTP file server
            cls._server = HTTPServer(('127.0.0.1', cls._port), TunnelMediaHandler)
            srv_thread = threading.Thread(target=cls._server.serve_forever, daemon=True)
            srv_thread.start()

            # 3. Open TLS tunnel via OpenSSH
            cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-R', f'80:localhost:{cls._port}', 'nokey@localhost.run']
            cls._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # 4. Parse public https URL
            start = time.time()
            while time.time() - start < 12:
                line = cls._proc.stdout.readline()
                if line:
                    m = re.search(r'https://[a-zA-Z0-9\.\-_]+\.lhr\.life', line)
                    if m:
                        cls._public_domain = m.group(0)
                        break

            if not cls._public_domain:
                raise RuntimeError("Failed to establish Zero-Card Public Tunnel. Check network/SSH access.")

            time.sleep(1.5) # Allow DNS propagation

    @classmethod
    def expose_file(cls, file_path: Path) -> str:
        cls.start_if_needed()
        file_path = Path(file_path).resolve()
        filename = file_path.name
        cls._file_mapping[filename] = str(file_path)
        return f"{cls._public_domain}/{filename}"

    @classmethod
    def close(cls):
        with cls._lock:
            if cls._proc:
                try:
                    cls._proc.terminate()
                except Exception:
                    pass
                cls._proc = None
            if cls._server:
                try:
                    cls._server.shutdown()
                except Exception:
                    pass
                cls._server = None
            cls._public_domain = None
            cls._file_mapping.clear()

class CloudBridge:
    """
    Automated temporary cloud storage bridge for Meta Graph API ingestion.
    Supports:
    1. ZeroCardTunnel (Default: 100% Free, NO credit card, instant HTTPS)
    2. Cloudflare R2 / AWS S3 / MinIO
    3. Local Simulation Mode (for dry-run testing)
    """

    def __init__(self):
        self.provider = STORAGE_PROVIDER.lower()
        self.bucket = S3_BUCKET_NAME
        self.public_prefix = S3_PUBLIC_URL_PREFIX.rstrip("/") if S3_PUBLIC_URL_PREFIX else None
        self.presigned_ttl = S3_PRESIGNED_TTL
        self.s3_client = None

        if self.is_cloud_configured():
            self._init_s3_client()

    def is_cloud_configured(self) -> bool:
        """Checks if S3/R2 cloud storage credentials are configured."""
        if self.provider == "tunnel":
            return False
        return bool(
            self.bucket 
            and not self.bucket.startswith("YOUR_")
            and (
                (AWS_ACCESS_KEY_ID and not AWS_ACCESS_KEY_ID.startswith("YOUR_"))
                or (S3_ENDPOINT_URL and S3_ENDPOINT_URL.startswith("http") and not S3_ENDPOINT_URL.startswith("https://<"))
            )
        )

    def _init_s3_client(self):
        """Initializes boto3 client compatible with AWS S3, Cloudflare R2, and MinIO."""
        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
            "config": Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"}
            )
        }
        if S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = S3_ENDPOINT_URL
        if S3_REGION_NAME and S3_REGION_NAME != "auto":
            client_kwargs["region_name"] = S3_REGION_NAME

        self.s3_client = boto3.client(**client_kwargs)

    def upload_file(self, local_path: Path, object_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Uploads/Exposes a local media file to provide a public HTTPS URL for Meta ingestion.
        """
        local_path = Path(local_path).resolve()
        if not local_path.exists():
            raise FileNotFoundError(f"File to upload not found: {local_path}")

        ext = local_path.suffix.lower()
        content_type = mimetypes.guess_type(str(local_path))[0] or "video/mp4"

        # 1. Zero-Card Public Tunnel Bridge (Default when no paid S3/R2 configured)
        if self.provider == "tunnel" or not self.is_cloud_configured():
            print(f"[CloudBridge] 🌐 Exposing {local_path.name} via Zero-Card Public HTTPS Tunnel...")
            try:
                public_url = ZeroCardTunnelBridge.expose_file(local_path)
                print(f"[CloudBridge] ✅ Live Public Ingestion URL: {public_url}")
                return {
                    "success": True,
                    "url": public_url,
                    "object_key": local_path.name,
                    "provider": "zero_card_tunnel",
                    "bucket": "localhost",
                    "is_simulated": False
                }
            except Exception as e:
                print(f"[CloudBridge Warning] Zero-Card Tunnel failed ({e}), falling back to simulated bridge.")

        # 2. Cloud Upload (S3 / Cloudflare R2 / MinIO)
        if self.is_cloud_configured() and self.s3_client:
            if not object_key:
                unique_id = uuid.uuid4().hex[:10]
                timestamp = int(time.time())
                object_key = f"instagram_reels/{timestamp}_{unique_id}{ext}"

            print(f"[CloudBridge] Uploading {local_path.name} to {self.bucket}/{object_key}...")
            extra_args = {"ContentType": content_type}
            self.s3_client.upload_file(str(local_path), self.bucket, object_key, ExtraArgs=extra_args)

            if self.public_prefix:
                public_url = f"{self.public_prefix}/{object_key}"
            else:
                public_url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": object_key},
                    ExpiresIn=self.presigned_ttl
                )

            return {
                "success": True,
                "url": public_url,
                "object_key": object_key,
                "provider": self.provider,
                "bucket": self.bucket,
                "is_simulated": False
            }

        # 3. Local Simulation Fallback
        simulated_key = f"simulated_reels/{local_path.name}"
        simulated_url = f"https://media.instagram-pipeline.local/{simulated_key}"
        return {
            "success": True,
            "url": simulated_url,
            "object_key": simulated_key,
            "provider": "local_simulation",
            "bucket": "local",
            "is_simulated": True
        }

    def delete_object(self, object_key: str) -> bool:
        """
        Cleans up the temporary object/tunnel once Meta has ingested the video.
        """
        if self.provider == "tunnel" or not self.is_cloud_configured():
            # Close the zero-card tunnel
            ZeroCardTunnelBridge.close()
            return True

        if not AUTO_DELETE_CLOUD_OBJECT or not self.s3_client:
            return True

        try:
            print(f"[CloudBridge] Deleting temporary cloud object: {object_key}...")
            self.s3_client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            print(f"[CloudBridge Warning] Failed to delete {object_key}: {e}")
            return False
