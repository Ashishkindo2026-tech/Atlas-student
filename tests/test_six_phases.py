"""Six-phase tests for Atlas Student."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain.student_reasoning import StudentReasoner
from planning.student_planner import StudentPlanner
from voice.student_voice import detect_hinglish
from vision.vision_client import VisionClient


class SixPhaseTests(unittest.TestCase):
    def test_reasoning_identifies_missing_constraints(self):
        plan = StudentReasoner().analyze("make me a study plan")
        self.assertEqual(plan.intent, "study_planning")
        self.assertIn("time", plan.missing)
        self.assertIn("subject", plan.missing)

    def test_planner_respects_total_minutes(self):
        blocks = StudentPlanner().build("Physics", 45)
        self.assertEqual(sum(block.minutes for block in blocks), 45)

    def test_voice_detects_hinglish(self):
        self.assertTrue(detect_hinglish("mujhe physics ka revision karna hai"))
        self.assertFalse(detect_hinglish("Explain Newton's second law"))

    def test_vision_encodes_local_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tiny.bin"
            path.write_bytes(b"atlas")
            encoded = VisionClient.encode_image(str(path))
            self.assertEqual(encoded, "YXRsYXM=")

    def test_vision_rejects_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            VisionClient.encode_image("does-not-exist.png")


if __name__ == "__main__":
    unittest.main()
