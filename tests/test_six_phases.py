"""Six-phase tests for Atlas Student."""
import tempfile
import unittest
from pathlib import Path

from brain.student_reasoning import StudentReasoner
from memory.student_memory import StudentMemory
from planning.student_planner import StudentPlanner
from privacy.privacy_shield import PrivacyShield
from voice.student_voice import detect_hinglish
from vision.vision_client import VisionClient


class SixPhaseTests(unittest.TestCase):
    def test_reasoning_identifies_missing_constraints(self):
        plan = StudentReasoner().analyze("make me a study plan")
        self.assertEqual(plan.intent, "study_planning")
        self.assertIn("time", plan.missing)
        self.assertIn("subject", plan.missing)

    def test_planner_respects_total_minutes(self):
        for minutes in (1, 15, 45, 46, 90, 120):
            blocks = StudentPlanner().build("Physics", minutes)
            self.assertEqual(sum(block.minutes for block in blocks), minutes)

    def test_memory_requires_consent(self):
        memory = StudentMemory()
        self.assertFalse(memory.remember("temporary test fact", approved=False))

    def test_privacy_redacts_secrets(self):
        shield = PrivacyShield()
        self.assertIn("[REDACTED]", shield.redact("api_key=abc123"))

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
