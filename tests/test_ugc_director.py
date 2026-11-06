"""
Unit tests for UGC Lifestyle & Product Ad Director.
Verifies consistency tokens, product fidelity (glass bottle vs tumbler),
and 6-beat UGC narrative architecture.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from video.brain.ugc_director import UGCDirector, DEFAULT_CREATOR, DEFAULT_PRODUCT


class TestUGCDirector(unittest.TestCase):
    """Verifies UGC ad structure, creator identity, and product fidelity."""

    def test_default_creator_consistency(self):
        """Verifies creator profile contains key features and consistency token."""
        c = DEFAULT_CREATOR
        self.assertIn("Elena", c["name"])
        self.assertIn("pink hair clip", c["accessory"])
        self.assertIn("dark brunette", c["hair"])
        self.assertIn("pastel-pink", c["outfit"])
        self.assertIn("Elena", c["consistency_token"])

    def test_default_product_fidelity(self):
        """Verifies product is specified as a glass bottle and not a tumbler."""
        p = DEFAULT_PRODUCT
        self.assertEqual(p["brand"], "SOLPOPA")
        self.assertEqual(p["flavor"], "Mango Soda")
        self.assertEqual(p["packaging_type"], "glass_bottle")
        self.assertIn("glass", p["bottle_description"])
        self.assertIn("bottle", p["bottle_description"])
        self.assertIn("not a tumbler", p["consistency_token"])

    def test_create_solpopa_blueprint(self):
        """Verifies 6-beat UGC narrative architecture."""
        bp = UGCDirector.create_solpopa_blueprint()
        self.assertIn("SOLPOPA", bp["title"])
        self.assertEqual(len(bp["scenes"]), 6)

        expected_beats = [
            "Hook",
            "Product Reveal",
            "First Impression & Inspection",
            "Opening & Fizz",
            "First Sip & Reaction",
            "Product Hero & Call to Action"
        ]
        actual_beats = [s["beat_name"] for s in bp["scenes"]]
        self.assertEqual(actual_beats, expected_beats)

        # Check SFX cues, dialogue, and prompts
        for idx, scene in enumerate(bp["scenes"]):
            self.assertTrue(len(scene["spoken_dialogue"]) > 0)
            self.assertTrue(len(scene["visual_prompt"]) > 0)
            self.assertTrue(len(scene["sfx"]) > 0)
            self.assertTrue(len(scene["on_screen_text"]) > 0)
            self.assertIn("SOLPOPA", scene["visual_prompt"])
            if idx in (0, 2, 4, 5):  # Creator on-camera shots
                self.assertIn("Elena", scene["visual_prompt"])

        # Check total duration is within 25-30 seconds
        self.assertGreaterEqual(bp["duration_sec"], 25.0)
        self.assertLessEqual(bp["duration_sec"], 30.0)

    def test_export_blueprint_files(self):
        """Verifies exporting blueprint JSON and Markdown brief."""
        bp = UGCDirector.create_solpopa_blueprint()
        json_path, md_path = UGCDirector.export_blueprint_files(bp, output_prefix="test_ugc_solpopa")

        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())

        # Cleanup test artifacts
        json_path.unlink()
        md_path.unlink()


if __name__ == "__main__":
    unittest.main()
