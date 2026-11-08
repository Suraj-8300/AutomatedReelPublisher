"""
Tests for VideoAnalyzer module in AutoReelStudio.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json
import shutil

from video.video_analyzer import VideoAnalyzer, _extract_json


class TestVideoAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.dummy_video = self.test_dir / "test_sample_video.mp4"
        # Write 100KB dummy file
        with open(self.dummy_video, "wb") as f:
            f.write(b"\x00" * 102400)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_extract_json_valid(self):
        sample = '{"title": "Awesome Cat", "summary": "A cat doing bakery"}'
        res = _extract_json(sample)
        self.assertEqual(res.get("title"), "Awesome Cat")

    def test_extract_json_fenced(self):
        sample = """Here is the JSON:
```json
{
  "title": "Fenced Cat",
  "hook": "Wait till you see this!"
}
```
Hope you like it!"""
        res = _extract_json(sample)
        self.assertEqual(res.get("title"), "Fenced Cat")
        self.assertEqual(res.get("hook"), "Wait till you see this!")

    def test_extract_json_broken(self):
        res = _extract_json("not valid json at all")
        self.assertEqual(res, {})

    @patch("video.cdn_optimizer.CDNOptimizer.probe_video")
    @patch("subprocess.run")
    def test_generate_thumbnail_and_keyframes(self, mock_subproc, mock_probe):
        mock_probe.return_value = {
            "valid": True,
            "duration": 15.0,
            "size_mb": 2.5,
            "video": {"width": 1080, "height": 1920, "codec": "h264"}
        }
        mock_subproc.return_value = MagicMock(returncode=0)

        # Create expected thumbnail
        expected_thumb = self.test_dir / "test_sample_video_thumb.jpg"
        with open(expected_thumb, "wb") as f:
            f.write(b"fake_jpg_content_123456789")

        res_thumb = VideoAnalyzer.generate_thumbnail(self.dummy_video)
        self.assertEqual(res_thumb, expected_thumb)

    @patch("video.cdn_optimizer.CDNOptimizer.probe_video")
    def test_analyze_video_heuristic_fallback(self, mock_probe):
        mock_probe.return_value = {
            "valid": True,
            "duration": 10.0,
            "size_mb": 1.2,
            "video": {"width": 1080, "height": 1920, "codec": "h264"}
        }

        # Analyze without Gemini key or with error
        with patch("video.video_analyzer.GEMINI_API_KEY", ""):
            metadata = VideoAnalyzer.analyze_video(self.dummy_video)

        self.assertEqual(metadata["filename"], "test_sample_video.mp4")
        self.assertIn("Test Sample Video", metadata["title"])
        self.assertIn("Double tap", metadata["instagram_caption"])
        self.assertTrue(len(metadata["hashtags"]) > 0)

        # Companion JSON check
        companion_file = self.test_dir / "test_sample_video.json"
        self.assertTrue(companion_file.exists())
        with open(companion_file, "r") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["filename"], "test_sample_video.mp4")

    def test_get_video_metadata_cached(self):
        companion_file = self.test_dir / "test_sample_video.json"
        with open(companion_file, "w") as f:
            json.dump({
                "title": "Cached Title",
                "summary": "Cached Summary",
                "hashtags": ["#Test"]
            }, f)

        meta = VideoAnalyzer.get_video_metadata(self.dummy_video)
        self.assertEqual(meta["title"], "Cached Title")
        self.assertEqual(meta["summary"], "Cached Summary")


if __name__ == "__main__":
    unittest.main()
