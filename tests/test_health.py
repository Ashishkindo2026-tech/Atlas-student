import unittest
from unittest.mock import Mock

from health.diagnostics import run_health_checks


class HealthDiagnosticsTests(unittest.TestCase):
    def test_healthy_ollama(self):
        client = Mock()
        client.status.return_value = {
            "service": True,
            "model": "qwen2.5:1.5b",
            "model_available": True,
            "url": "http://localhost:11434",
        }
        result = run_health_checks(client)
        self.assertEqual(result["status"], "healthy")

    def test_offline_ollama_is_degraded_not_crash(self):
        client = Mock()
        client.status.return_value = {
            "service": False,
            "model": "qwen2.5:1.5b",
            "model_available": False,
            "url": "http://localhost:11434",
        }
        result = run_health_checks(client)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["checks"][0]["status"], "offline")


if __name__ == "__main__":
    unittest.main()
