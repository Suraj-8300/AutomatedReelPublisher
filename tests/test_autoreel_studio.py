#!/usr/bin/env python3
"""
Unit and integration tests for AutoReelStudio (Merged ReelMakerAI + ReelPublisher).
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.creative_randomizer import CreativeRandomizer, GENRE_TAXONOMY, GENERATION_MODES
from core.content_history import ContentHistory
from core.hooks_engine import HooksEngine
from core.idea_generator import IdeaGenerator
from core.cache_manager import CacheManager
from instagram_pipeline.preprocessor import VideoPreprocessor

class TestAutoReelStudio(unittest.TestCase):

    def test_backwards_compatibility_symlinks(self):
        """Verifies that ReelMakerAI and ReelPublisher symlinks exist and resolve to AutoReelStudio."""
        projects_dir = PROJECT_ROOT.parent
        reel_maker = projects_dir / "ReelMakerAI"
        reel_publisher = projects_dir / "ReelPublisher"
        auto_reel_studio = projects_dir / "AutoReelStudio"

        self.assertTrue(reel_maker.exists(), "ReelMakerAI symlink must exist")
        self.assertTrue(reel_publisher.exists(), "ReelPublisher symlink must exist")
        self.assertTrue(auto_reel_studio.is_dir(), "AutoReelStudio must be a valid directory")

        self.assertEqual(reel_maker.resolve(), auto_reel_studio.resolve(),
                         "ReelMakerAI must resolve to AutoReelStudio")
        self.assertEqual(reel_publisher.resolve(), auto_reel_studio.resolve(),
                         "ReelPublisher must resolve to AutoReelStudio")

    def test_unified_cli_parser(self):
        """Verifies that autoreel.py can parse subcommands correctly."""
        import subprocess
        res = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "autoreel.py"), "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("AutoReelStudio", res.stdout)
        self.assertIn("make", res.stdout)
        self.assertIn("publish", res.stdout)
        self.assertIn("studio", res.stdout)
        self.assertIn("auto", res.stdout)
        self.assertIn("check", res.stdout)
        self.assertIn("clean", res.stdout)
        self.assertIn("topics", res.stdout)

    def test_cache_telemetry(self):
        """Verifies cache manager telemetry and GC stats."""
        stats = CacheManager.get_cache_stats()
        self.assertIn("total_mb", stats)
        self.assertIn("file_count", stats)
        self.assertIsInstance(stats["total_mb"], (int, float))

    def test_smart_idea_ranking(self):
        """Verifies idea candidates ranking from ReelMakerAI subsystem."""
        ideas = IdeaGenerator.generate_idea_candidates(
            genre="science", duration=15, count=3, seed=123
        )
        self.assertEqual(len(ideas), 3)
        for idea in ideas:
            self.assertEqual(idea["genre"], "science")
            self.assertGreaterEqual(idea["retention_score"], 0)
            self.assertLessEqual(idea["retention_score"], 100)

    def test_compliance_validator(self):
        """Verifies video compliance validation logic from ReelPublisher subsystem."""
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

        # Non-compliant check
        bad_meta = {
            "duration": 120.0,  # Exceeds max 90s
            "file_size": 1500 * 1024 * 1024,  # Exceeds max size
            "faststart": False,
            "video": {"present": True, "codec": "hevc", "width": 1920, "height": 1080, "fps": 120.0, "pix_fmt": "yuv420p"},
            "audio": {"present": True, "codec": "mp3", "sample_rate": 44100, "channels": 1}
        }
        bad_res = VideoPreprocessor.validate_compliance(bad_meta)
        self.assertFalse(bad_res["is_compliant"])
        self.assertGreaterEqual(len(bad_res["issues"]), 3)

if __name__ == "__main__":
    unittest.main()
