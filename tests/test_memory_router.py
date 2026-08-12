import unittest

from brain.memory_router import MemoryRouter


class MemoryRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = MemoryRouter()

    def test_remember_requires_explicit_memory_request(self):
        result = self.router.route("remember that I prefer concise answers")
        self.assertEqual(result, {
            "type": "memory_request",
            "value": "I prefer concise answers",
        })

    def test_normal_conversation_is_not_memory(self):
        result = self.router.route("I prefer concise answers")
        self.assertEqual(result["type"], "conversation")

    def test_forget_request_is_routed(self):
        result = self.router.route("forget my preferred response style")
        self.assertEqual(result, {
            "type": "forget_request",
            "value": "my preferred response style",
        })

    def test_show_and_forget_all_commands(self):
        self.assertEqual(self.router.route("show memory")["type"], "show_memory")
        self.assertEqual(self.router.route("forget everything")["type"], "forget_all")


if __name__ == "__main__":
    unittest.main()
