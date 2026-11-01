import time
import uuid
import requests
from typing import Dict, Any, Optional

from .config import (
    META_API_BASE_URL,
    INSTAGRAM_ACCOUNT_ID,
    META_ACCESS_TOKEN,
    META_API_TIMEOUT,
    CONTAINER_POLL_INTERVAL,
    CONTAINER_POLL_TIMEOUT
)

class MetaGraphPublisher:
    """
    Official Meta Graph API client for automated Instagram Reels publishing.
    Implements container initialization, status polling, and publication trigger.
    """

    def __init__(self, account_id: Optional[str] = None, access_token: Optional[str] = None):
        self.account_id = account_id or INSTAGRAM_ACCOUNT_ID
        self.access_token = access_token or META_ACCESS_TOKEN
        self.base_url = META_API_BASE_URL
        self.timeout = META_API_TIMEOUT
        self.poll_interval = CONTAINER_POLL_INTERVAL
        self.poll_timeout = CONTAINER_POLL_TIMEOUT

    def is_configured(self) -> bool:
        """Verifies if Meta Graph API account ID and access token are provided."""
        return bool(self.account_id and self.access_token)

    def create_reel_container(
        self,
        video_url: str,
        caption: str,
        share_to_feed: bool = True,
        thumb_offset_ms: int = 1000,
        cover_url: Optional[str] = None,
        dry_run: bool = False
    ) -> str:
        """
        Step 1: Creates an Instagram Reel container on Meta Graph API.
        POST /{ig-user-id}/media
        """
        if dry_run or not self.is_configured():
            sim_container_id = f"1799{uuid.uuid4().int % 1000000000:09d}"
            print(f"[MetaGraphAPI (Dry-Run)] POST /{self.account_id or 'mock_account'}/media")
            print(f"                       media_type=REELS, video_url={video_url[:60]}...")
            print(f"                       Container created: {sim_container_id}")
            return sim_container_id

        url = f"{self.base_url}/{self.account_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": share_to_feed,
            "thumb_offset": thumb_offset_ms,
            "access_token": self.access_token
        }
        if cover_url:
            payload["cover_url"] = cover_url

        response = requests.post(url, data=payload, timeout=self.timeout)
        data = response.json()

        if response.status_code != 200 or "id" not in data:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Meta Graph API container creation failed (HTTP {response.status_code}): {error_msg}")

        container_id = data["id"]
        print(f"[MetaGraphAPI] Reel container created: {container_id}")
        return container_id

    def poll_container_status(self, container_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Step 2: Polls status of container until FINISHED or ERROR.
        GET /{container-id}?fields=status_code,status
        """
        if dry_run or not self.is_configured():
            print(f"[MetaGraphAPI (Dry-Run)] GET /{container_id}?fields=status_code,status")
            time.sleep(1.0)
            print("[MetaGraphAPI (Dry-Run)] Status: IN_PROGRESS (ingesting & transcoding...)")
            time.sleep(1.0)
            print("[MetaGraphAPI (Dry-Run)] Status: FINISHED (ready for publication)")
            return {"status_code": "FINISHED", "status": "Ready to publish"}

        url = f"{self.base_url}/{container_id}"
        params = {
            "fields": "status_code,status",
            "access_token": self.access_token
        }

        start_time = time.time()
        while time.time() - start_time < self.poll_timeout:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            status_code = data.get("status_code", "UNKNOWN")
            status_desc = data.get("status", "")

            print(f"[MetaGraphAPI] Polling container {container_id}: {status_code} ({status_desc or 'processing'})...")

            if status_code == "FINISHED":
                return data
            elif status_code == "ERROR":
                raise RuntimeError(f"Meta container ingestion failed: {status_desc or data}")
            elif status_code == "EXPIRED":
                raise RuntimeError(f"Meta container expired before publishing: {status_desc or data}")

            time.sleep(self.poll_interval)

        raise TimeoutError(f"Container {container_id} ingestion timed out after {self.poll_timeout}s.")

    def publish_reel(self, container_id: str, dry_run: bool = False) -> str:
        """
        Step 3: Triggers final publication of the validated Reel.
        POST /{ig-user-id}/media_publish?creation_id={container_id}
        """
        if dry_run or not self.is_configured():
            sim_media_id = f"1800{uuid.uuid4().int % 1000000000:09d}"
            print(f"[MetaGraphAPI (Dry-Run)] POST /{self.account_id or 'mock_account'}/media_publish")
            print(f"                       creation_id={container_id}")
            print(f"                       Reel published successfully! Media ID: {sim_media_id}")
            return sim_media_id

        url = f"{self.base_url}/{self.account_id}/media_publish"
        payload = {
            "creation_id": container_id,
            "access_token": self.access_token
        }

        response = requests.post(url, data=payload, timeout=self.timeout)
        data = response.json()

        if response.status_code != 200 or "id" not in data:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Meta Graph API publication failed (HTTP {response.status_code}): {error_msg}")

        media_id = data["id"]
        print(f"[MetaGraphAPI] 🎉 Reel published live! Media ID: {media_id}")
        return media_id

    def get_reel_permalink(self, media_id: str, dry_run: bool = False) -> str:
        """
        Step 4: Fetches the public Instagram URL permalink for the published Reel.
        GET /{media-id}?fields=permalink
        """
        if dry_run or not self.is_configured():
            sim_code = uuid.uuid4().hex[:11]
            return f"https://www.instagram.com/reel/{sim_code}/"

        url = f"{self.base_url}/{media_id}"
        params = {
            "fields": "permalink",
            "access_token": self.access_token
        }
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
            return data.get("permalink", f"https://www.instagram.com/{media_id}")
        except Exception:
            return f"https://www.instagram.com/{media_id}"

    def publish_pipeline(
        self,
        video_url: str,
        caption: str,
        share_to_feed: bool = True,
        thumb_offset_ms: int = 1000,
        cover_url: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the full Meta Graph API Reels publication pipeline:
        Container Creation -> Status Validation -> Media Publish -> Permalink Retrieval
        """
        print("\n[MetaGraphAPI] Initiating Instagram Reels publication sequence...")
        
        # 1. Create Container
        container_id = self.create_reel_container(
            video_url=video_url,
            caption=caption,
            share_to_feed=share_to_feed,
            thumb_offset_ms=thumb_offset_ms,
            cover_url=cover_url,
            dry_run=dry_run
        )

        # 2. Poll Container Status
        status_info = self.poll_container_status(container_id, dry_run=dry_run)

        # 3. Trigger Publication
        media_id = self.publish_reel(container_id, dry_run=dry_run)

        # 4. Fetch Permalink
        permalink = self.get_reel_permalink(media_id, dry_run=dry_run)

        return {
            "success": True,
            "container_id": container_id,
            "media_id": media_id,
            "permalink": permalink,
            "status_info": status_info,
            "is_simulated": dry_run or not self.is_configured()
        }

    def get_account_info(self) -> Dict[str, Any]:
        """Fetches basic profile info (username, id) of the connected Instagram account."""
        if not self.is_configured():
            return {"id": self.account_id, "username": "sun_27417"}
        url = f"{self.base_url}/{self.account_id}?fields=id,name,username&access_token={self.access_token}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {"id": self.account_id, "username": "sun_27417"}

    def get_publishing_limit(self) -> Dict[str, Any]:
        """Fetches daily 24h Reels publishing quota usage for the account."""
        if not self.is_configured():
            return {"quota_usage": 0, "quota_total": 100, "quota_duration": 86400}
        url = f"{self.base_url}/{self.account_id}/content_publishing_limit?fields=config,quota_usage&access_token={self.access_token}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                records = data.get("data", [])
                if records:
                    rec = records[0]
                    cfg = rec.get("config", {})
                    return {
                        "quota_usage": rec.get("quota_usage", 0),
                        "quota_total": cfg.get("quota_total", 100),
                        "quota_duration": cfg.get("quota_duration", 86400)
                    }
        except Exception:
            pass
        return {"quota_usage": 0, "quota_total": 100, "quota_duration": 86400}


