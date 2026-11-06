"""
Unit tests for Two-Stage Gemini Viral Idea Generator and Synchronized Script Generation.
"""

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from video.brain.idea_generator import IdeaGenerator
from video.visuals.broll import BRollEngine, SYNONYM_MAP


class TestIdeaGenerator(unittest.TestCase):
    """Verifies two-stage viral idea generation and entity binding."""

    @patch("video.brain.idea_generator._call_gemini")
    def test_generate_viral_prompt(self, mock_gemini):
        mock_gemini.return_value = """
        {
            "topic": "The Abandoned Pup's New Journey",
            "subject_entity": "golden retriever puppy",
            "viral_prompt": "A tiny golden retriever pup shivering under a porch finds food, gentle hands, and a joyful new home.",
            "target_emotion": "heartwarming",
            "voice_style": "female",
            "music_style": "heartwarming_story"
        }
        """
        idea = IdeaGenerator.generate_viral_prompt(pillar="animal_story")
        self.assertEqual(idea["topic"], "The Abandoned Pup's New Journey")
        self.assertEqual(idea["subject_entity"], "golden retriever puppy")
        self.assertEqual(idea["target_emotion"], "heartwarming")

    @patch("video.brain.idea_generator._call_gemini")
    def test_generate_synchronized_reel_idea(self, mock_gemini):
        # Return Stage 1 prompt on first call, Stage 2 script on second call
        mock_gemini.side_effect = [
            """{
                "topic": "The Rescued Duckling",
                "subject_entity": "baby duckling",
                "viral_prompt": "A baby duckling separated from its mother is sheltered, fed, and reunited with its flock.",
                "target_emotion": "heartwarming",
                "voice_style": "female",
                "music_style": "heartwarming_story"
            }""",
            """{
                "title": "The Rescued Duckling",
                "subject_entity": "baby duckling",
                "hook": "A lost duckling cried out alone by the roadside.",
                "escalation": "Kind volunteers scooped him up and warmed him gently with a soft towel. Within an hour, he was chirping happily.",
                "payoff": "Today, he swims safely with his flock in the pond.",
                "voice_style": "female",
                "music_style": "heartwarming_story",
                "scenes": [
                    {
                        "scene_num": 1,
                        "text": "A lost duckling cried out alone by the roadside.",
                        "visual_action": "Baby duckling alone on the ground",
                        "search_queries": ["baby duckling alone", "duckling"]
                    },
                    {
                        "scene_num": 2,
                        "text": "Kind volunteers scooped him up and warmed him gently with a soft towel.",
                        "visual_action": "Hands holding baby duckling gently",
                        "search_queries": ["holding baby duckling", "petting duck"]
                    },
                    {
                        "scene_num": 3,
                        "text": "Today, he swims safely with his flock in the pond.",
                        "visual_action": "Duckling swimming in pond",
                        "search_queries": ["duckling swimming", "ducks in pond"]
                    }
                ]
            }"""
        ]

        script = IdeaGenerator.generate_synchronized_reel_idea(pillar="animal_story")
        self.assertEqual(script["topic"], "The Rescued Duckling")
        self.assertEqual(script["subject_entity"], "baby duckling")
        self.assertEqual(len(script["scenes"]), 3)
        self.assertIn("A lost duckling cried out", script["narration"])

        # Verify that all search queries contain the subject entity or related action
        for scene in script["scenes"]:
            self.assertTrue(len(scene["keywords"]) > 0)
            self.assertTrue(any("duck" in kw.lower() for kw in scene["keywords"]))

    def test_broll_synonym_map_has_no_generic_office_terms(self):
        """Verifies that SYNONYM_MAP does not route human actions to disconnected corporate stock."""
        for key in ["hands", "petting", "feeding", "holding"]:
            synonyms = SYNONYM_MAP.get(key, [])
            for syn in synonyms:
                self.assertNotIn("laptop", syn)
                self.assertNotIn("typing", syn)
                self.assertNotIn("office", syn)
                self.assertNotIn("meeting", syn)


if __name__ == "__main__":
    unittest.main()
