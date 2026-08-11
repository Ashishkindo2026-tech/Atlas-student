import unittest
from learning.learning_signal_detector import detect
from hardware.manager import HardwareManager
from hardware.devices import SimulatedSpeaker


class LearningSignalTests(unittest.TestCase):
    def test_understood_signal(self):
        signal = detect("Now I understand Newton's third law", "Newton's Third Law")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, "understood")
        self.assertEqual(signal.concept, "Newton's Third Law")

    def test_difficulty_signal(self):
        signal = detect("I still don't understand friction", "Friction")
        self.assertIsNotNone(signal)
        self.assertEqual(signal.kind, "difficulty")

    def test_neutral_text_does_not_change_progress(self):
        self.assertIsNone(detect("Explain friction", "Friction"))


class HardwareTests(unittest.TestCase):
    def test_permission_blocks_device(self):
        manager = HardwareManager()
        manager.register(SimulatedSpeaker())
        with self.assertRaises(PermissionError):
            manager.execute("simulated_speaker", "speak", text="hello")

    def test_permission_allows_device(self):
        manager = HardwareManager()
        manager.register(SimulatedSpeaker())
        manager.set_permission("audio_output", True)
        result = manager.execute("simulated_speaker", "speak", text="hello")
        self.assertEqual(result["spoken"], "hello")


if __name__ == "__main__":
    unittest.main()
