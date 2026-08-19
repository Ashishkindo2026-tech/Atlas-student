import unittest
from unittest.mock import Mock, patch

import requests

from llm.ollama_client import Ollama_Client


class OllamaClientTests(unittest.TestCase):
    def test_empty_prompt_is_handled_without_network_call(self):
        client = Ollama_Client(retries=0)
        with patch("llm.ollama_client.requests.post") as post:
            result = client.ask("   ")
        self.assertIn("need a message", result.lower())
        post.assert_not_called()

    def test_connection_failure_returns_recoverable_message(self):
        client = Ollama_Client(retries=1)
        with patch(
            "llm.ollama_client.requests.post",
            side_effect=requests.ConnectionError("connection refused"),
        ) as post:
            result = client.ask("hello")
        self.assertIn("can't reach ollama", result.lower())
        self.assertEqual(post.call_count, 2)

    def test_http_404_identifies_missing_model(self):
        client = Ollama_Client(model="missing:model", retries=0)
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError(
            response=Mock(status_code=404)
        )
        with patch("llm.ollama_client.requests.post", return_value=response):
            result = client.ask("hello")
        self.assertIn("missing:model", result)
        self.assertIn("not available", result.lower())

    def test_success_returns_trimmed_response(self):
        client = Ollama_Client(retries=0)
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"response": "  Hello Atlas.  "}
        with patch("llm.ollama_client.requests.post", return_value=response):
            result = client.ask("hello")
        self.assertEqual(result, "Hello Atlas.")

    def test_health_check_does_not_raise_on_network_failure(self):
        client = Ollama_Client()
        with patch(
            "llm.ollama_client.requests.get",
            side_effect=requests.ConnectionError("offline"),
        ):
            self.assertFalse(client.health_check())


if __name__ == "__main__":
    unittest.main()
