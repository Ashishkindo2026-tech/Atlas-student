import unittest
from unittest.mock import Mock, patch

import requests

from llm.ollama_client import OllamaError, Ollama_Client


class OllamaClientTests(unittest.TestCase):
    def test_configuration_defaults(self):
        client = Ollama_Client()
        self.assertTrue(client.model)
        self.assertEqual(client.generate_url, "http://localhost:11434/api/generate")

    @patch("llm.ollama_client.requests.Session.post")
    def test_successful_response_is_stripped(self, post):
        response = Mock()
        response.json.return_value = {"response": "  hello Atlas  "}
        response.raise_for_status.return_value = None
        post.return_value = response

        self.assertEqual(Ollama_Client().ask("hello"), "hello Atlas")
        post.assert_called_once()

    @patch("llm.ollama_client.requests.Session.post")
    def test_http_failure_becomes_ollama_error(self, post):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("500")
        post.return_value = response

        with self.assertRaises(OllamaError):
            Ollama_Client(retries=0).ask("hello")

    @patch("llm.ollama_client.requests.Session.post", side_effect=requests.ConnectionError())
    def test_connection_failure_is_explicit(self, _post):
        with self.assertRaisesRegex(OllamaError, "unavailable"):
            Ollama_Client(retries=0).ask("hello")

    @patch("llm.ollama_client.requests.Session.post", side_effect=requests.Timeout())
    def test_timeout_is_explicit(self, _post):
        with self.assertRaisesRegex(OllamaError, "timed out"):
            Ollama_Client(retries=0, timeout=2).ask("hello")

    @patch("llm.ollama_client.requests.Session.post")
    def test_model_error_is_not_returned_as_chat_text(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"error": "model not found"}
        post.return_value = response

        with self.assertRaisesRegex(OllamaError, "model not found"):
            Ollama_Client().ask("hello")

    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(ValueError):
            Ollama_Client().ask("   ")


if __name__ == "__main__":
    unittest.main()
