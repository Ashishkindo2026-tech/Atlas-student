import unittest
from unittest.mock import patch

from beta.live_student_beta import start_beta


class LiveStudentBetaLauncherTests(unittest.TestCase):
    @patch("beta.live_student_beta.run_voice_mode")
    @patch("beta.live_student_beta.Ollama_Client")
    @patch("beta.live_student_beta.scan_and_ingest", return_value=[])
    def test_launcher_starts_real_voice_mode(self, scan, client, voice_mode):
        start_beta()
        client.assert_called_once_with()
        voice_mode.assert_called_once_with(client.return_value)
        scan.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
