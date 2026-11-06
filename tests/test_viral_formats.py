"""
Unit tests for Viral Format Catalog and AI Video Engine.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from video.brain.viral_format_catalog import ViralFormatCatalog, VIRAL_FORMATS
from video.visuals.veo import VeoVideoEngine


class TestViralFormats(unittest.TestCase):
    """Verifies all 6 viral formats and templates are properly defined."""

    def test_catalog_has_all_six_formats(self):
        formats = ViralFormatCatalog.list_formats()
        expected = [
            "anthropomorphic_animal",
            "ai_baby_adult",
            "brainrot_meme",
            "animal_cinematic_story",
            "impossible_asmr",
            "cinematic_pov",
        ]
        for exp in expected:
            self.assertIn(exp, formats)

    def test_anthropomorphic_animal_templates(self):
        cat_waiter = ViralFormatCatalog.get_template("anthropomorphic_animal", "british_cat_waiter")
        self.assertEqual(cat_waiter["id"], "british_cat_waiter")
        self.assertIn("British Shorthair", cat_waiter["character"])
        self.assertIn("9:16", cat_waiter["video_prompt"])

    def test_ai_baby_templates(self):
        baby_golgappa = ViralFormatCatalog.get_template("ai_baby_adult", "baby_golgappa_stall")
        self.assertEqual(baby_golgappa["id"], "baby_golgappa_stall")
        self.assertIn("street food", baby_golgappa["hook"].lower())

    def test_brainrot_templates(self):
        ballerina = ViralFormatCatalog.get_template("brainrot_meme", "ballerina_cappuccina")
        self.assertEqual(ballerina["id"], "ballerina_cappuccina")
        self.assertIn("cappuccino", ballerina["character"].lower())

    def test_veo_availability_check(self):
        # Should gracefully return boolean without raising an exception
        res = VeoVideoEngine.is_veo_available()
        self.assertIsInstance(res, bool)


if __name__ == "__main__":
    unittest.main()
