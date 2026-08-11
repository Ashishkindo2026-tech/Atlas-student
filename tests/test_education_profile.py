import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from education.student_profile import EducationProfile
from education.agent_bridge import education_context


class EducationProfileTests(unittest.TestCase):
    def test_profile_defaults_and_customization(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            with patch("education.student_profile.FILE", path):
                profile = EducationProfile()
                data = profile.data()
                self.assertEqual(data["board"], "CBSE")
                self.assertEqual(data["core_classes"], [9, 10, 11, 12])
                self.assertEqual(data["optional_classes"], [1, 2, 3, 4, 5, 6, 7, 8])
                self.assertTrue(profile.set_class(11))
                self.assertTrue(profile.set_subject("Physics"))
                context = profile.context()
                self.assertIn("Primary class: 11", context)
                self.assertIn("Primary subject: Physics", context)
                self.assertIn("Core curriculum: Classes 9-12", context)
                self.assertIn("Classes 1-8: optional user-provided material", context)

    def test_invalid_class_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            with patch("education.student_profile.FILE", path):
                self.assertFalse(EducationProfile().set_class(13))

    def test_bridge_includes_education_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            with patch("education.student_profile.FILE", path):
                profile = EducationProfile()
                profile.set_class(10)
                profile.set_subject("Mathematics")
                context = education_context("quadratic equations")
                self.assertIn("Board: CBSE", context)
                self.assertIn("Primary class: 10", context)
                self.assertIn("Primary subject: Mathematics", context)
                self.assertIn("EDUCATION RETRIEVAL", context)


if __name__ == "__main__":
    unittest.main()
