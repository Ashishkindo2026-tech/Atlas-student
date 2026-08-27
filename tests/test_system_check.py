import unittest
from unittest.mock import patch

from tools import system_check


class SystemCheckTests(unittest.TestCase):
    def test_module_check_reports_import_failure_without_crashing(self):
        with patch("importlib.import_module", side_effect=ImportError("missing")):
            result = system_check._module("example")
        self.assertFalse(result.ok)
        self.assertIn("missing", result.detail)

    @patch("tools.system_check.urlopen")
    def test_ollama_reports_service_and_model(self, urlopen):
        class Response:
            def __init__(self, payload):
                self.payload = payload
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                import json
                return json.dumps(self.payload).encode()

        urlopen.side_effect = [Response({"version": "0.1"}), Response({"models": [{"name": "qwen2.5:1.5b"}]})]
        with patch("atlas_core.config.CONFIG.ollama_base_url", "http://127.0.0.1:11434"), patch("atlas_core.config.CONFIG.ollama_model", "qwen2.5:1.5b"):
            results = system_check._ollama()
        self.assertTrue(all(item.ok for item in results))

    @patch("tools.system_check.urlopen", side_effect=OSError("offline"))
    def test_ollama_offline_is_reported(self, _urlopen):
        results = system_check._ollama()
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].ok)
        self.assertIn("unavailable", results[0].detail)


if __name__ == "__main__":
    unittest.main()
