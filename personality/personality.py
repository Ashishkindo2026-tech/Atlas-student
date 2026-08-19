import json
import os
from datetime import datetime

from core.safe_storage import atomic_write_text, file_lock

BASE_FILE = "personality/personality.json"
ADAPTATION_FILE = "personality/adaptation.json"


class Personality:
    """Atlas personality core plus a persistent, user-controlled adaptation layer."""

    def __init__(self):
        self.data = self._load_json(BASE_FILE, {})
        self.adaptation = self._load_json(ADAPTATION_FILE, self._default_adaptation())

    def _load_json(self, path, default):
        try:
            with file_lock(path):
                with open(path, "r", encoding="utf-8") as f:
                    value = json.load(f)
                return value if isinstance(value, dict) else default
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            self._save_json(path, default)
            return default

    def _save_json(self, path, value):
        with file_lock(path):
            atomic_write_text(path, json.dumps(value, indent=4, ensure_ascii=False))

    def _default_adaptation(self):
        return {"preferences": {key: {"value": value, "confidence": 0.0, "source": "none", "last_confirmed": None, "context": context} for key, value, context in [
            ("verbosity", "balanced", "general"), ("technical_depth", "adaptive", "general"),
            ("humor", "adaptive", "general"), ("language", "adaptive", "general"),
            ("examples", "adaptive", "learning"), ("step_by_step", "adaptive", "learning")
        ]}}

    def get(self):
        return self.data

    def get_adaptation(self):
        return self.adaptation

    def observe(self, user_text):
        """Learn only from explicit interaction signals, not sensitive inference."""
        text = user_text.lower().strip()
        observations = []
        rules = [
            (("verbosity", "concise", "explicit feedback", "general"), ["just the answer", "keep it short", "be concise", "short answer", "stop yapping", "too long"]),
            (("verbosity", "detailed", "explicit feedback", "general"), ["explain in detail", "go deeper", "more detail", "deep explanation", "explain fully"]),
            (("technical_depth", "high", "explicit request", "technical"), ["use technical terms", "technical detail", "technical explanation", "show the architecture"]),
            (("technical_depth", "low", "explicit request", "learning"), ["simple words", "explain simply", "easy words", "i don't understand"]),
            (("humor", "high", "explicit request", "general"), ["be funny", "make it funny", "use humor"]),
            (("humor", "low", "explicit feedback", "general"), ["no jokes", "don't joke", "stop joking"]),
            (("language", "hinglish", "explicit request", "general"), ["speak hinglish", "reply in hinglish", "use hinglish"]),
            (("language", "hindi", "explicit request", "general"), ["speak hindi", "reply in hindi"]),
            (("language", "english", "explicit request", "general"), ["speak english", "reply in english"]),
            (("examples", "preferred", "explicit request", "learning"), ["give examples", "with examples", "use examples"]),
            (("step_by_step", "preferred", "explicit request", "learning"), ["step by step", "step-by-step", "one step at a time"]),
        ]
        for observation, phrases in rules:
            if any(p in text for p in phrases):
                observations.append(observation)
        for key, value, source, context in observations:
            self._update_preference(key, value, source, context)
        return observations

    def _update_preference(self, key, value, source, context):
        with file_lock(ADAPTATION_FILE):
            pref = self.adaptation.setdefault("preferences", {}).setdefault(key, {"value": "adaptive", "confidence": 0.0, "source": "none", "last_confirmed": None, "context": context})
            old_value = pref.get("value")
            old_confidence = float(pref.get("confidence", 0.0))
            confidence = min(1.0, old_confidence + 0.12) if old_value == value else (0.55 if old_confidence < 0.5 else min(1.0, old_confidence + 0.05))
            pref.update({"value": value, "confidence": round(confidence, 2), "source": source, "last_confirmed": datetime.now().isoformat(timespec="seconds"), "context": context})
            atomic_write_text(ADAPTATION_FILE, json.dumps(self.adaptation, indent=4, ensure_ascii=False))

    def reset(self):
        self.adaptation = self._default_adaptation()
        self._save_json(ADAPTATION_FILE, self.adaptation)

    def explain(self):
        lines = [f"- {key}: {item['value']} ({int(item['confidence'] * 100)}% confidence; context: {item.get('context', 'general')})" for key, item in self.adaptation.get("preferences", {}).items() if item.get("confidence", 0) > 0]
        return "\n".join(lines) if lines else "I haven't learned any response preferences yet."

    def prompt_block(self, user_text):
        self.observe(user_text)
        preferences = self.adaptation.get("preferences", {})
        active = [f"{key}={item.get('value')} ({int(item.get('confidence', 0) * 100)}% confidence, {item.get('context', 'general')})" for key, item in preferences.items() if float(item.get("confidence", 0)) >= 0.55]
        lower = user_text.lower()
        context = "technical" if any(word in lower for word in ["code", "python", "program", "architecture", "debug", "github", "api"]) else "learning" if any(word in lower for word in ["study", "learn", "explain", "homework", "physics", "math", "chapter"]) else "planning" if any(word in lower for word in ["plan", "schedule", "goal", "decision"]) else "general"
        return "PERSONALITY ADAPTATION:\n" + f"Current context: {context}\nLearned preferences (soft guidance, never absolute):\n" + ("\n".join(f"- {x}" for x in active) if active else "- No reliable preferences yet.") + "\nAdapt expression to the user, but never change Atlas's core values, honesty, privacy, safety, or user control."
