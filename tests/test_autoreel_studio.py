#!/usr/bin/env python3
"""
Comprehensive Modular Architecture Unit Tests for AutoReelStudio.
Tests:
  1. idea_generation: 10-15 idea queue buffer, replenishment, research synthesis
  2. video_generation: 50 reels/day quota governor, visual & audio parameters
  3. video_processing: CDN faststart check & metadata packager for IG and YT
  4. publishers: Instagram compliance validator & YouTube OAuth flow
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from idea_generation import IdeaQueueManager, IdeaResearchEngine, MIN_QUEUE_THRESHOLD, TARGET_QUEUE_SIZE
from video_generation import QuotaGovernor, DAILY_MAX_REELS, AIVisualEngine
from video_processing import CDNOptimizer, MetadataPackager
from publishers.instagram.preprocessor import VideoPreprocessor
from publishers.youtube.auth import YouTubeAuthenticator
from publishers.dispatch_queue import PublishingQueueManager
from publishers.recent_manager import RecentlyPublishedManager, MAX_RECENT_PUBLISHED

class TestAutoReelStudioModularArchitecture(unittest.TestCase):

    def test_idea_queue_replenishment_and_buffer(self):
        """Verifies the 10-15 idea buffer replenishment rule."""
        # 1. Replenish
        res = IdeaQueueManager.replenish_if_needed()
        count = IdeaQueueManager.get_count()
        self.assertGreaterEqual(count, MIN_QUEUE_THRESHOLD)
        self.assertLessEqual(count, TARGET_QUEUE_SIZE)

        # 2. When >= 10, generation must pause
        res2 = IdeaQueueManager.replenish_if_needed()
        self.assertEqual(res2["action"], "paused")

        # 3. Pop an idea
        idea = IdeaQueueManager.pop_next_idea(auto_replenish=False)
        self.assertIsNotNone(idea)
        self.assertIn("hook", idea)
        self.assertIn("scenes", idea)
        self.assertGreaterEqual(len(idea["scenes"]), 2)

    def test_daily_quota_governor(self):
        """Verifies the 50 reels/day safety limit and telemetry."""
        status = QuotaGovernor.get_status()
        self.assertEqual(status["daily_limit"], 50)
        self.assertIn("generated_today", status)
        self.assertIn("remaining_today", status)
        self.assertEqual(status["remaining_today"], 50 - status["generated_today"])

        allowed, remaining, msg = QuotaGovernor.can_generate()
        self.assertTrue(allowed)
        self.assertGreater(remaining, 0)

    def test_manual_override_and_auto_publish_cutoff(self):
        """Verifies 1-Click Publish Now override (+20 reels) and auto-publish cutoff rule."""
        import tempfile
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_quota_file = Path(tf.name)
            temp_quota_file.write_text("{}", encoding="utf-8")

        try:
            with patch("video_generation.quota_governor.QUOTA_FILE", temp_quota_file):
                # 1. Baseline status
                status = QuotaGovernor.get_status()
                self.assertEqual(status["daily_limit"], 50)
                self.assertEqual(status["manual_limit"], 20)
                self.assertEqual(status["total_limit"], 70)
                self.assertFalse(status["auto_publish_stopped"])

                # Auto publish should initially be allowed
                auto_allowed, msg = QuotaGovernor.is_auto_publish_allowed()
                self.assertTrue(auto_allowed)

                # 2. Record 1-Click Manual Publish
                QuotaGovernor.record_publish(is_manual=True)
                updated = QuotaGovernor.get_status()
                self.assertEqual(updated["manual_published_today"], 1)
                self.assertTrue(updated["auto_publish_stopped"])

                # Auto publish MUST now be halted for today
                auto_allowed_now, stop_reason = QuotaGovernor.is_auto_publish_allowed()
                self.assertFalse(auto_allowed_now)
                self.assertIn("stopped", stop_reason.lower())

                # Manual override should still have 19 remaining
                can_manual, remaining_m, _ = QuotaGovernor.can_manual_publish()
                self.assertTrue(can_manual)
                self.assertEqual(remaining_m, 19)

                # 3. Test reaching 20 manual limit
                for _ in range(19):
                    QuotaGovernor.record_publish(is_manual=True)

                can_manual_20, remaining_m20, cap_msg = QuotaGovernor.can_manual_publish()
                self.assertFalse(can_manual_20)
                self.assertEqual(remaining_m20, 0)
                self.assertIn("ceiling reached", cap_msg.lower())

                # 4. Resume auto-publish manually
                QuotaGovernor.resume_auto_publish()
                resumed_status = QuotaGovernor.get_status()
                self.assertFalse(resumed_status["auto_publish_stopped"])
        finally:
            temp_quota_file.unlink(missing_ok=True)

    def test_ten_minute_interval_pacing(self):
        """Verifies the 10-minute queue pacing interval."""
        from publishers.dispatch_queue import DEFAULT_INTERVAL_MINUTES
        self.assertEqual(DEFAULT_INTERVAL_MINUTES, 10.0)

    def test_metadata_packager_platforms(self):
        """Verifies tailored metadata generation for Instagram and YouTube."""
        title = "The Quantum Eraser Reality"
        hook = "Physicists proved light can change its past."
        facts = "Delayed choice photon experiment."
        payoff = "Time is not a one way street."

        # Instagram Package
        ig_pkg = MetadataPackager.package_for_instagram(
            title=title, genre="science_paradoxes", hook=hook, facts=facts, payoff=payoff
        )
        self.assertIn("#reels", ig_pkg["caption"])
        self.assertIn(hook, ig_pkg["caption"])

        # YouTube Package
        yt_pkg = MetadataPackager.package_for_youtube(
            title=title, genre="science_paradoxes", hook=hook, facts=facts, payoff=payoff
        )
        self.assertTrue(yt_pkg["title"].endswith("#Shorts"))
        self.assertLessEqual(len(yt_pkg["title"]), 100)
        self.assertEqual(yt_pkg["category_id"], "28")
        self.assertIn("Shorts", yt_pkg["tags"])

    def test_instagram_compliance_audit(self):
        """Verifies Instagram technical specifications validation."""
        compliant_meta = {
            "duration": 15.0,
            "file_size": 15 * 1024 * 1024,
            "faststart": True,
            "video": {
                "present": True,
                "codec": "h264",
                "width": 1080,
                "height": 1920,
                "fps": 30.0,
                "pix_fmt": "yuv420p"
            },
            "audio": {
                "present": True,
                "codec": "aac",
                "sample_rate": 48000,
                "channels": 2
            }
        }
        res = VideoPreprocessor.validate_compliance(compliant_meta)
        self.assertTrue(res["is_compliant"])
        self.assertEqual(len(res["issues"]), 0)

    def test_youtube_oauth_configuration(self):
        """Verifies YouTube OAuth client flow and authorization URL generation."""
        auth_url, state = YouTubeAuthenticator.get_authorization_url()
        self.assertIn("accounts.google.com", auth_url)
        self.assertIn("198990477835-2s5o6ggf09a3d0uqmdlhvs9f0aa5nc4l", auth_url)
        self.assertIn("redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fyoutube%2Fcallback", auth_url)
        self.assertIn("youtube.upload", auth_url)

    def test_ai_visual_motion_clip_specs(self):
        """Verifies that the AI visual engine produces 1080x1920 9:16 vertical video motion clips."""
        dummy_img = Path(PROJECT_ROOT) / "cache" / "test_frame.jpg"
        if not dummy_img.exists():
            AIVisualEngine._render_procedural_fallback_image(prompt="AI Motion Test", output_path=dummy_img, seed=101)

        clip = AIVisualEngine.render_motion_clip(dummy_img, duration=0.5, motion="zoom_in")
        self.assertTrue(clip.exists())
        self.assertGreater(clip.stat().st_size, 1000)

        probe = CDNOptimizer.probe_video(clip)
        self.assertTrue(probe["valid"])
        self.assertEqual(probe["video"]["width"], 1080)
        self.assertEqual(probe["video"]["height"], 1920)

    def test_publishing_queue_pacing_and_upload_now(self):
        """Verifies ready videos scheduled queue, pacing intervals, and dry-run instant release."""
        dummy_video = Path(PROJECT_ROOT) / "output" / "test_queue_reel.mp4"
        dummy_video.touch()

        # Enqueue item
        item = PublishingQueueManager.enqueue(
            video_path=dummy_video,
            title="Scheduled Paced Test Reel",
            platforms=["instagram", "youtube"]
        )
        self.assertIn("pub_", item["id"])
        self.assertEqual(item["status"], "scheduled")
        self.assertIn("scheduled_time", item)

        # Retrieve queue
        queue = PublishingQueueManager.get_queue()
        ids = [i["id"] for i in queue]
        self.assertIn(item["id"], ids)

        # Cancel/cleanup
        PublishingQueueManager.cancel_item(item["id"])
        item_updated = PublishingQueueManager.get_item(item["id"])
        self.assertEqual(item_updated["status"], "cancelled")
        PublishingQueueManager.clear_completed()
        dummy_video.unlink(missing_ok=True)

    def test_recently_published_rolling_10_and_pruning(self):
        """Verifies rolling window of 10 published reels and physical disk deletion of pruned reels."""
        import tempfile
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_json_path = Path(tf.name)
            temp_json_path.write_text("[]", encoding="utf-8")

        test_old_file = Path(PROJECT_ROOT) / "output" / "test_prune_old_reel_9999.mp4"
        test_old_file.touch()

        try:
            with patch("publishers.recent_manager.RECENT_PUBLISHED_FILE", temp_json_path):
                # Seed with test_old_file
                RecentlyPublishedManager.record_published({
                    "id": "pub_oldest_9999",
                    "title": "Oldest Pruned Reel",
                    "filename": test_old_file.name,
                    "video_path": str(test_old_file),
                    "platforms": ["youtube"],
                    "published_at": "2026-11-01T00:00:00Z"
                })

                # Add 10 new items to push the oldest item out of the rolling 10 buffer
                for i in range(10):
                    RecentlyPublishedManager.record_published({
                        "id": f"pub_test_filler_{i}",
                        "title": f"Recent Reel {i}",
                        "filename": f"dummy_{i}.mp4",
                        "video_path": f"/tmp/dummy_{i}.mp4",
                        "platforms": ["instagram", "youtube"],
                        "published_at": f"2026-11-05T0{i}:00:00Z"
                    })

                recent = RecentlyPublishedManager.get_recent(limit=20)
                self.assertEqual(len(recent), MAX_RECENT_PUBLISHED)
                self.assertNotIn("pub_oldest_9999", [r["id"] for r in recent])
                self.assertFalse(test_old_file.exists())
        finally:
            temp_json_path.unlink(missing_ok=True)
            test_old_file.unlink(missing_ok=True)

    def test_universe_manager_episodic_continuity(self):
        """Verifies the 2026 Persistent Character Universe & 3-Act Narrative Architecture."""
        from core.universe_manager import UniverseManager, UNIVERSES

        # 1. Universes existence
        universes = UniverseManager.get_all_universes()
        self.assertIn("mochi_and_friends", universes)
        self.assertIn("baby_boss_ventures", universes)
        self.assertIn("emotional_animal_sagas", universes)
        self.assertIn("fictional_pov", universes)
        self.assertIn("visual_asmr_satisfaction", universes)

        # 2. Generate episode and verify 3-act structure
        ep = UniverseManager.generate_next_episode(universe_id="mochi_and_friends")
        self.assertIn("title", ep)
        self.assertIn("hook", ep)
        self.assertIn("script", ep)
        self.assertIn("scenes", ep)
        self.assertGreaterEqual(len(ep["scenes"]), 3)
        self.assertIn("narrative_structure", ep)
        self.assertIn("act1_hook", ep["narrative_structure"])
        self.assertIn("act2_escalation", ep["narrative_structure"])
        self.assertIn("act3_payoff", ep["narrative_structure"])

        # 3. Switching active universe
        success = UniverseManager.set_active_universe("baby_boss_ventures")
        self.assertTrue(success)
        active_info = UniverseManager.get_active_universe_info()
        self.assertEqual(active_info["universe_id"], "baby_boss_ventures")

        # Revert back
        UniverseManager.set_active_universe("mochi_and_friends")

if __name__ == "__main__":
    unittest.main()
