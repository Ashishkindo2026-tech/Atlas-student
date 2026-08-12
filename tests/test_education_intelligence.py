import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from education.intelligence import EducationIntelligence
from education.student_profile import EducationProfile


class EducationIntelligenceTests(unittest.TestCase):
    def test_explicit_request_overrides_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile_file = Path(tmp) / "student_profile.json"
            with patch("education.student_profile.FILE", profile_file):
                profile = EducationProfile()
                profile.set_class(11)
                profile.set_subject("Physics")
                intelligence = EducationIntelligence(profile=profile)
                with patch("education.intelligence.retrieve", return_value=[]):
                    state = intelligence.analyze("Help me with Class 10 mathematics")
                self.assertEqual(state["class_level"], 10)
                self.assertEqual(state["subject"], "Mathematics")

    def test_learning_evidence_is_filtered_to_subject(self):
        intelligence = EducationIntelligence()
        progress = {
            "learning_signals": [
                {"kind": "difficulty", "subject": "Physics", "evidence": "hard"},
                {"kind": "understood", "subject": "Chemistry", "evidence": "clear"},
            ]
        }
        with patch("education.intelligence.retrieve", return_value=[]):
            state = intelligence.analyze("Explain physics", progress)
        self.assertEqual(len(state["learning_evidence"]), 1)
        self.assertEqual(state["learning_evidence"][0]["subject"], "Physics")

    def test_missing_constraints_are_not_invented(self):
        intelligence = EducationIntelligence()
        with patch("education.intelligence.retrieve", return_value=[]):
            state = intelligence.analyze("Explain this concept")
        self.assertIsNone(state["class_level"])
        self.assertIsNone(state["subject"])
        self.assertTrue(state["needs_class"])
        self.assertTrue(state["needs_subject"])
        context = intelligence.prompt_context(state)
        self.assertIn("Class: not explicitly set", context)
        self.assertIn("Subject: not explicitly set", context)

    def test_retrieval_state_and_source_locations_are_preserved(self):
        intelligence = EducationIntelligence()
        material = [{"text": "source text", "page": 42, "chapter": "1", "section": "1.1", "source": "NCERT Physics", "score": 1.0}]
        with patch("education.intelligence.retrieve", return_value=material):
            state = intelligence.analyze("Explain force in physics")
        self.assertTrue(state["material_found"])
        self.assertEqual(state["retrieval"][0]["page"], 42)
        self.assertIn("NCERT Physics | page 42", intelligence.prompt_context(state))


if __name__ == "__main__":
    unittest.main()
