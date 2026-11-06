"""
Unit tests for Consistent Character Story Engine & Character Director.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from PIL import Image

from video.brain.character_director import CharacterDirector
from video.visuals.consistent_story import ConsistentStoryEngine, fit_to_vertical
from video.config import CACHE_DIR, TARGET_WIDTH, TARGET_HEIGHT


class TestConsistentStory(unittest.TestCase):

    def test_character_profile_generation(self):
        profile = CharacterDirector.create_character_profile(species="kitten", seed=100)
        self.assertIn("character_token", profile)
        self.assertIn("setting", profile)
        self.assertIn("markings", profile)
        self.assertIn("accessory", profile)
        self.assertEqual(profile["species"], "kitten")
        self.assertTrue(profile["character_token"].startswith("a photorealistic"))

    def test_fit_to_vertical(self):
        # Create a horizontal image (800x600)
        im = Image.new("RGB", (800, 600), color=(255, 100, 50))
        vertical = fit_to_vertical(im, target_w=540, target_h=960)
        self.assertEqual(vertical.size, (540, 960))

    @patch("video.visuals.consistent_story.requests.get")
    def test_fetch_scene_frame_mock(self, mock_get):
        # Create dummy JPEG bytes
        im = Image.new("RGB", (100, 100), color=(100, 200, 50))
        from io import BytesIO
        buf = BytesIO()
        im.save(buf, "JPEG")
        dummy_bytes = buf.getvalue()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = dummy_bytes * 100  # >10000 bytes
        mock_get.return_value = mock_resp

        frame = ConsistentStoryEngine.fetch_scene_frame(
            prompt="test kitten baking bread",
            seed=42,
            scene_idx=0,
            total_scenes=3,
            retries=1
        )
        self.assertIsNotNone(frame)
        self.assertTrue(frame.exists())

    def test_cinematic_crop_creation(self):
        # Create a dummy test image
        test_img_path = CACHE_DIR / "test_master_frame.jpg"
        im = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), color=(50, 100, 200))
        im.save(test_img_path, "JPEG")

        medium_crop = ConsistentStoryEngine.create_cinematic_crop(test_img_path, crop_type="medium")
        self.assertTrue(medium_crop.exists())
        with Image.open(medium_crop) as im_m:
            self.assertEqual(im_m.size, (TARGET_WIDTH, TARGET_HEIGHT))

        close_up_crop = ConsistentStoryEngine.create_cinematic_crop(test_img_path, crop_type="close_up")
        self.assertTrue(close_up_crop.exists())
        with Image.open(close_up_crop) as im_c:
            self.assertEqual(im_c.size, (TARGET_WIDTH, TARGET_HEIGHT))


if __name__ == "__main__":
    unittest.main()
