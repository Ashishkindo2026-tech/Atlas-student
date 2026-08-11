import json
import os
from datetime import datetime


BASE_FILE = "personality/personality.json"
ADAPTATION_FILE = "personality/adaptation.json"


class Personality:
    """Atlas personality core plus a persistent, user-controlled adaptation layer."""

    def __init__(self):
        self.data = self._load_json(BASE_FILE, {})
        self.adaptation = self._load_json(ADAPTATION_FILE, self._default_adaptation())

    def _load_json(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                value = json.load(f)
                return value if isinstance(value, dict) else default
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self._save_json(path, default)
            return default

    def _save_json(self, path, value):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        temp = f"{path}.tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=4, ensure_ascii=False)
        os.replace(temp, path)

    def _default_adaptation(self):
        return {
            "preferences": {
                key: {
                    "value": value,
                    "confidence": 0.0,
                    "source": "none",
                    "last_confirmed": None,
                    "context": context,
                }
                for key, value, context in [
                    ("verbosity", "balanced", "general"),
                    ("technical_depth", "adaptive", "general"),
                    ("humor", "adaptive", "general"),
                    ("language", "adaptive", "general"),
                    ("examples", "adaptive", "learning"),
                    ("step_by_step", "adaptive", "learning"),
                ]
            }
        }

    def get(self):
        return self.data

    def get_adaptation(self):
        return self.adaptation

    def observe(self, user_text):
        """Learn only from explicit interaction signals, not sensitive inference."""
        text = user_text.lower().strip()
        observations = []

        if any(p in text for p in ["just the answer", "keep it short", "be concise", "short answer", "stop yapping", "too long"]):
            observations.append(("verbosity", "concise", "explicit feedback", "general"))
        elif any(p in text for p in ["explain in detail", "go deeper", "more detail", "deep explanation", "explain fully"]):
            observations.append(("verbosity", "detailed", "explicit feedback", "general"))

        if any(p in text for p in ["use technical terms", "technical detail", "technical explanation", "show the architecture"]):
            observations.append(("technical_depth", "high", "explicit request", "technical"))
        elif any(p in text for p in ["simple words", "explain simply", "easy words", "i don't understand"]):
            observations.append(("technical_depth", "low", "explicit request", "learning"))

        if any(p in text for p in ["be funny", "make it funny", "use humor"]):
            observations.append(("humor", "high", "explicit request", "general"))
        elif any(p in text for p in ["no jokes", "don't joke", "stop joking"]):
            observations.append(("humor", "low", "explicit feedback", "general"))

        if any(p in text for p in ["speak hinglish", "reply in hinglish", "use hinglish"]):
            observations.append(("language", "hinglish", "explicit request", "general"))
        elif any(p in text for p in ["speak hindi", "reply in hindi"]):
            observations.append(("language", "hindi", "explicit request", "general"))
        elif any(p in text for p in ["speak english", "reply in english"]):
            observations.append(("language", "english", "explicit request", "general"))

        if any(p in text for p in ["give examples", "with examples", "use examples"]):
            observations.append(("examples", "preferred", "explicit request", "learning"))
        if any(p in text for p in ["step by step", "step-by-step", "one step at a time"]):
            observations.append(("step_by_step", "preferred", "explicit request", "learning"))

        for key, value, source, context in observations:
            self._update_preference(key, value, source, context)

        return observations

    def _update_preference(self, key, value, source, context):
        pref = self.adaptation.setdefault("preferences", {}).setdefault(
            key,
            {"value": "adaptive", "confidence": 0.0, "source": "none", "last_confirmed": None, "context": context},
        )
        old_value = pref.get("value")
        old_confidence = float(pref.get("confidence", 0.0))

        if old_value == value:
            confidence = min(1.0, old_confidence + 0.12)
        else:
            confidence = 0.55 if old_confidence < 0.5 else min(1.0, old_confidence + 0.05)

        pref.update({
            "value": value,
            "confidence": round(confidence, 2),
            "source": source,
            "last_confirmed": datetime.now().isoformat(timespec="seconds"),
            "context": context,
        })
        self._save_json(ADAPTATION_FILE, self.adaptation)

    def reset(self):
        self.adaptation = self._default_adaptation()
        self._save_json(ADAPTATION_FILE, self.adaptation)

    def explain(self):
        lines = []
        for key, item in self.adaptation.get("preferences", {}).items():
            if item.get("confidence", 0) > 0:
                lines.append(
                    f"- {key}: {item['value']} "
                    f"({int(item['confidence'] * 100)}% confidence; "
                    f"context: {item.get('context', 'general')})"
                )
        return "\n".join(lines) if lines else "I haven't learned any response preferences yet."

    def prompt_block(self, user_text):
        """Return only adaptation guidance; core values remain immutable."""
        self.observe(user_text)
        preferences = self.adaptation.get("preferences", {})
        active = []
        for key, item in preferences.items():
            if float(item.get("confidence", 0)) >= 0.55:
                active.append(f"{key}={item.get('value')} ({int(item.get('confidence', 0) * 100)}% confidence, {item.get('context', 'general')})")

        context = "general"
        lower = user_text.lower()
        if any(word in lower for word in ["code", "python", "program", "architecture", "debug", "github", "api"]):
            context = "technical"
        elif any(word in lower for word in ["study", "learn", "explain", "homework", "physics", "math", "chapter"]):
            context = "learning"
        elif any(word in lower for word in ["plan", "schedule", "goal", "decision"]):
            context = "planning"

        return (
            "PERSONALITY ADAPTATION:\n"
            f"Current context: {context}\n"
            "Learned preferences (soft guidance, never absolute):\n"
            + ("\n".join(f"- {x}" for x in active) if active else "- No reliable preferences yet.")
            + "\nAdapt expression to the user, but never change Atlas's core values, honesty, privacy, safety, or user control."
        )
