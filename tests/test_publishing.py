"""
Test Suite for Direct YouTube & Instagram Publishing Pipeline
Tests platform publishers, OAuth, compliance auditor, and metadata packager.
Zero queue rules, zero pacing delays.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from instagram import (
    InstagramPublisher,
    VideoPreprocessor
)
from youtube import (
    YouTubePublisher,
    YouTubeAuthenticator
)
from video import CDNOptimizer, MetadataPackager


class TestDirectPublishing(unittest.TestCase):
    """Verifies YouTube and Instagram publishing credentials, metadata, and compliance."""

    def test_youtube_oauth_configuration(self):
        """Verifies YouTube OAuth client flow and authorization URL generation."""
        auth_url, state = YouTubeAuthenticator.get_authorization_url()
        self.assertIn("accounts.google.com", auth_url)
        self.assertIn("198990477835-2s5o6ggf09a3d0uqmdlhvs9f0aa5nc4l", auth_url)
        self.assertIn("youtube.upload", auth_url)

    def test_youtube_service_authenticated(self):
        """Verifies YouTube client can authenticate and retrieve channel info."""
        service = YouTubeAuthenticator.get_authenticated_service()
        self.assertIsNotNone(service)
        channels = service.channels().list(mine=True, part="snippet").execute()
        items = channels.get("items", [])
        self.assertGreater(len(items), 0)
        self.assertEqual(items[0]["snippet"]["title"], "EGO X")

    def test_instagram_configured(self):
        """Verifies Instagram Meta Graph publisher configuration."""
        pub = InstagramPublisher()
        self.assertTrue(pub.is_configured())
        self.assertEqual(pub.account_id, "17841476861770479")

    def test_instagram_dry_run_container(self):
        """Verifies Instagram dry-run container creation."""
        pub = InstagramPublisher()
        sim_id, upload_uri = pub.create_resumable_container(caption="Test Caption", dry_run=True)
        self.assertTrue(sim_id.startswith("1799"))
        self.assertIn("rupload.facebook.com", upload_uri)

    def test_metadata_packager_platforms(self):
        """Verifies tailored metadata generation for Instagram and YouTube."""
        title = "The Kitten and the Firefly"
        hook = "He was freezing..."
        facts = "A tiny orange kitten discovers a trapped firefly."
        payoff = "Kindness returns when you need it most."

        # Instagram Package
        ig_pkg = MetadataPackager.package_for_instagram(
            title=title, genre="emotional_story", hook=hook, facts=facts, payoff=payoff
        )
        self.assertIn("#reels", ig_pkg["caption"])
        self.assertIn(hook, ig_pkg["caption"])

        # YouTube Package
        yt_pkg = MetadataPackager.package_for_youtube(
            title=title, genre="emotional_story", hook=hook, facts=facts, payoff=payoff
        )
        self.assertTrue(yt_pkg["title"].endswith("#Shorts"))
        self.assertLessEqual(len(yt_pkg["title"]), 100)
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

    def test_topic_rotator_schedule(self):
        """Verifies daily schedule generation and pillar heuristic detection."""
        from video.sources import TopicRotator
        schedule = TopicRotator.get_daily_schedule(10)
        self.assertEqual(len(schedule), 10)
        self.assertEqual(TopicRotator.detect_pillar("How a jet engine works"), "mechanical")
        self.assertEqual(TopicRotator.detect_pillar("Fourier Transform equation"), "explainer")
        self.assertEqual(TopicRotator.detect_pillar("A black hole collision"), "cinematic")

    def test_procedural_music_generation(self):
        """Verifies 48kHz procedural stereo music generation."""
        from video.audio import MusicEngine
        music_path = MusicEngine.generate(style="cyber_pulse", duration_sec=3.0)
        self.assertTrue(music_path.exists())
        self.assertGreater(music_path.stat().st_size, 5000)


if __name__ == "__main__":
    unittest.main()
