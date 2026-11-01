import os
import time
import shutil
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import (
    INBOX_DIR,
    PROCESSING_DIR,
    ARCHIVE_DIR,
    FAILED_DIR,
    DEFAULT_SCALING_MODE
)
from .preprocessor import VideoPreprocessor
from .metadata_linker import MetadataLinker
from .cloud_bridge import CloudBridge
from .publisher import MetaGraphPublisher

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".wmv", ".m4v"}

class ReelQueueManager:
    """
    Orchestrates the entire end-to-end Instagram Reels pipeline:
    Inbox Scanning -> File Stability Check -> Metadata Extraction ->
    FFmpeg Normalization -> Cloud Ingestion Bridge -> Meta Graph API Publishing ->
    Cloud Retention Cleanup -> Success Archiving / Failure Logging.
    """

    def __init__(
        self,
        inbox_dir: Path = INBOX_DIR,
        processing_dir: Path = PROCESSING_DIR,
        archive_dir: Path = ARCHIVE_DIR,
        failed_dir: Path = FAILED_DIR
    ):
        self.inbox_dir = Path(inbox_dir).resolve()
        self.processing_dir = Path(processing_dir).resolve()
        self.archive_dir = Path(archive_dir).resolve()
        self.failed_dir = Path(failed_dir).resolve()

        for d in [self.inbox_dir, self.processing_dir, self.archive_dir, self.failed_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.cloud_bridge = CloudBridge()
        self.publisher = MetaGraphPublisher()

    @staticmethod
    def is_file_stable(file_path: Path, wait_secs: float = 2.0) -> bool:
        """
        Ensures a newly dropped file has finished copying/downloading
        by verifying file size does not mutate over wait_secs.
        """
        try:
            initial_size = file_path.stat().st_size
            time.sleep(wait_secs)
            final_size = file_path.stat().st_size
            return initial_size == final_size and final_size > 0
        except OSError:
            return False

    def find_pending_videos(self) -> List[Path]:
        """Scans inbox directory for incoming footage files."""
        candidates = []
        for item in sorted(self.inbox_dir.iterdir()):
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                candidates.append(item)
        return candidates

    def process_video_file(
        self,
        raw_video_path: Path,
        scaling_mode: str = DEFAULT_SCALING_MODE,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the complete pipeline for a single video file.
        """
        raw_video_path = Path(raw_video_path).resolve()
        stem = raw_video_path.stem
        start_time = time.time()
        timestamp_prefix = time.strftime("%Y%m%d_%H%M%S")

        print("=" * 65)
        print(f"🎬 PROCESSING INSTAGRAM REEL CANDIDATE: {raw_video_path.name}")
        print("=" * 65)

        # 1. Verify file write completeness
        if not self.is_file_stable(raw_video_path):
            print(f"[QueueManager] File {raw_video_path.name} is still being written. Skipping for next cycle.")
            return {"success": False, "reason": "file_writing_in_progress"}

        # 2. Lock item by moving into processing directory
        proc_raw_video = self.processing_dir / raw_video_path.name
        try:
            shutil.move(str(raw_video_path), str(proc_raw_video))
        except Exception as e:
            print(f"[QueueManager Error] Failed to lock {raw_video_path.name} into processing: {e}")
            return {"success": False, "error": str(e)}

        # Also move any companion config files (.json, .txt, .jpg, .png)
        companion_files = []
        for ext in [".json", ".txt", ".jpg", ".jpeg", ".png"]:
            comp = raw_video_path.parent / f"{stem}{ext}"
            if comp.exists():
                target_comp = self.processing_dir / comp.name
                shutil.move(str(comp), str(target_comp))
                companion_files.append(target_comp)

        uploaded_object_key = None
        cover_object_key = None

        try:
            # 3. Metadata Extraction & Linking
            print("\n[Step 1/5] 📝 Extracting and Linking Metadata...")
            meta_info = MetadataLinker.link_metadata(proc_raw_video)
            print(f"           Caption Preview: \"{meta_info['caption'][:70]}...\"")
            print(f"           Share To Feed:   {meta_info['share_to_feed']}")

            # 4. Probe Compliance & Normalize with FFmpeg
            print("\n[Step 2/5] 🔍 Probing Compliance & Normalizing with FFmpeg...")
            source_probe = VideoPreprocessor.probe_video(proc_raw_video)
            compliance = VideoPreprocessor.validate_compliance(source_probe)

            normalized_path = self.processing_dir / f"{stem}_normalized.mp4"

            if compliance["is_compliant"]:
                print("           ✅ Input video is ALREADY 100% compliant with Instagram Reel specs.")
                # Fast copy or use directly
                shutil.copy(str(proc_raw_video), str(normalized_path))
            else:
                print(f"           ⚠️ Transcoding required. Issues found: {', '.join(compliance['issues'])}")
                print(f"           🎥 Transcoding using scaling mode: '{scaling_mode}'...")
                VideoPreprocessor.normalize_video(
                    input_path=proc_raw_video,
                    output_path=normalized_path,
                    scaling_mode=scaling_mode,
                    overwrite=True
                )
                print(f"           ✅ Successfully normalized: {normalized_path.name} (1080x1920 @ 30fps H.264/AAC)")

            # 5. Cloud Storage Bridge Upload
            print("\n[Step 3/5] ☁️ Uploading to Cloud Storage Bridge...")
            upload_res = self.cloud_bridge.upload_file(normalized_path)
            public_video_url = upload_res["url"]
            uploaded_object_key = upload_res.get("object_key")
            print(f"           Public Ingestion URL: {public_video_url}")

            # Optional custom cover upload
            cover_url = None
            if meta_info.get("cover_image"):
                cover_path = Path(meta_info["cover_image"])
                if cover_path.exists():
                    cover_upload = self.cloud_bridge.upload_file(cover_path)
                    cover_url = cover_upload["url"]
                    cover_object_key = cover_upload.get("object_key")
                    print(f"           Custom Cover URL: {cover_url}")

            # 6. Meta Graph API Publishing Sequence
            print("\n[Step 4/5] 🚀 Publishing to Instagram Reels via Meta Graph API...")
            pub_result = self.publisher.publish_pipeline(
                video_url=public_video_url,
                caption=meta_info["caption"],
                share_to_feed=meta_info["share_to_feed"],
                thumb_offset_ms=meta_info["thumb_offset_ms"],
                cover_url=cover_url,
                dry_run=dry_run
            )

            # 7. Cloud Storage Retention Cleanup
            print("\n[Step 5/5] 🧹 Cleaning up Temporary Cloud Storage Objects...")
            if uploaded_object_key:
                self.cloud_bridge.delete_object(uploaded_object_key)
            if cover_object_key:
                self.cloud_bridge.delete_object(cover_object_key)

            # 8. Archive Successful Publication
            archive_item_dir = self.archive_dir / f"{timestamp_prefix}_{stem}"
            archive_item_dir.mkdir(parents=True, exist_ok=True)

            shutil.move(str(normalized_path), str(archive_item_dir / normalized_path.name))
            shutil.move(str(proc_raw_video), str(archive_item_dir / proc_raw_video.name))
            for cf in companion_files:
                if cf.exists():
                    shutil.move(str(cf), str(archive_item_dir / cf.name))

            # Write publication receipt
            receipt = {
                "stem": stem,
                "published_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "instagram_media_id": pub_result.get("media_id"),
                "instagram_permalink": pub_result.get("permalink"),
                "caption": meta_info["caption"],
                "is_simulated": pub_result.get("is_simulated", False),
                "scaling_mode": scaling_mode
            }
            receipt_path = archive_item_dir / f"{stem}.published.json"
            with open(receipt_path, "w", encoding="utf-8") as f:
                json.dump(receipt, f, indent=2)

            print("\n" + "=" * 65)
            print(f"🎉 INSTAGRAM REEL PUBLISHED SUCCESSFULLY!")
            print(f"🔗 Permalink:  {receipt['instagram_permalink']}")
            print(f"📁 Archived:   {archive_item_dir}")
            print(f"⚡ Total Time: {receipt['elapsed_seconds']}s")
            print("=" * 65 + "\n")

            return {
                "success": True,
                "receipt": receipt,
                "archive_dir": str(archive_item_dir)
            }

        except Exception as err:
            print(f"\n❌ [QueueManager Failure] Error processing {stem}: {err}")
            traceback.print_exc()

            # Clean up cloud object if uploaded
            if uploaded_object_key:
                try:
                    self.cloud_bridge.delete_object(uploaded_object_key)
                except Exception:
                    pass
            if cover_object_key:
                try:
                    self.cloud_bridge.delete_object(cover_object_key)
                except Exception:
                    pass

            # Move to Failed Directory
            failed_item_dir = self.failed_dir / f"{timestamp_prefix}_{stem}"
            failed_item_dir.mkdir(parents=True, exist_ok=True)

            if proc_raw_video.exists():
                shutil.move(str(proc_raw_video), str(failed_item_dir / proc_raw_video.name))
            for cf in companion_files:
                if cf.exists():
                    shutil.move(str(cf), str(failed_item_dir / cf.name))

            # Write error log
            error_log_path = failed_item_dir / f"{stem}.error.log"
            with open(error_log_path, "w", encoding="utf-8") as f:
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
                f.write(f"Error: {str(err)}\n\n")
                f.write("Traceback:\n")
                f.write(traceback.format_exc())

            print(f"[QueueManager] Moved failed job to {failed_item_dir}\n")
            return {
                "success": False,
                "error": str(err),
                "failed_dir": str(failed_item_dir)
            }

    def process_inbox(self, scaling_mode: str = DEFAULT_SCALING_MODE, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Scans inbox and processes all queued video files."""
        pending = self.find_pending_videos()
        if not pending:
            return []

        print(f"[QueueManager] Found {len(pending)} video(s) in inbox: {[p.name for p in pending]}")
        results = []
        for p in pending:
            res = self.process_video_file(p, scaling_mode=scaling_mode, dry_run=dry_run)
            results.append(res)
        return results

    def watch_inbox(self, interval_secs: float = 5.0, scaling_mode: str = DEFAULT_SCALING_MODE, dry_run: bool = False):
        """
        Continuously watches inbox for incoming video reels.
        """
        print("=" * 65)
        print("👀 INSTAGRAM REELS MEDIA WATCHER DAEMON ACTIVE")
        print(f"📥 Watching Inbox:     {self.inbox_dir}")
        print(f"📦 Archive Directory: {self.archive_dir}")
        print(f"❌ Failed Directory:  {self.failed_dir}")
        print(f"⏱️ Check Interval:    {interval_secs}s")
        print(f"📐 Scaling Mode:       {scaling_mode}")
        print(f"🧪 Dry Run Mode:       {'ENABLED (Simulated)' if dry_run else 'DISABLED (Live Graph API)'}")
        print("=" * 65)

        try:
            while True:
                self.process_inbox(scaling_mode=scaling_mode, dry_run=dry_run)
                time.sleep(interval_secs)
        except KeyboardInterrupt:
            print("\n[Watcher] Daemon stopped by user.")

