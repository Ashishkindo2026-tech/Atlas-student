import importlib
import unittest


class ImportSmokeTests(unittest.TestCase):
    def test_core_modules_import(self):
        modules = [
            "brain.core",
            "brain.agent",
            "brain.memory_router",
            "memory.memory_manager",
            "personality.personality",
            "goals.goal_manager",
            "user.knowledge",
            "tools.tool_manager",
        ]
        for name in modules:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_student_gui_modules_import(self):
        """The desktop entrypoints must be import-safe in a clean CI install."""
        modules = [
            "gui.usage_tracker",
            "gui.first_launch",
            "gui.atlas_customizer",
            "gui.learning_os",
            "atlas_gui",
            "atlas_student",
        ]
        for name in modules:
            with self.subTest(module=name):
                importlib.import_module(name)


if __name__ == "__main__":
    unittest.main()
