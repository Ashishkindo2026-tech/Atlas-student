"""Unified facade for the six Atlas Student development phases."""
from __future__ import annotations
import json
from brain.student_intelligence import StudentIntelligence, AdaptiveLearning
from guidance.career import GuidanceEngine
from student.lifecycle import AtlasLifecycle


class PhaseEngine:
    def __init__(self):
        self.intelligence = StudentIntelligence()
        self.adaptive = AdaptiveLearning(self.intelligence)
        self.guidance = GuidanceEngine()
        self.lifecycle = AtlasLifecycle()

    def status(self): return self.lifecycle.status()

    def dashboard(self):
        return {"lifecycle": self.lifecycle.status(), "intelligence": self.intelligence.data(), "adaptive_path": self.adaptive.next_path()}

    def attempt(self, subject, topic, correct, difficulty=1): return self.intelligence.record_attempt(subject, topic, correct, difficulty)
    def mistake(self, subject, topic, error, correction=""): return self.intelligence.record_mistake(subject, topic, error, correction)
    def goal(self, goal, deadline="", target=""): return self.intelligence.set_goal(goal, deadline, target)
    def profile(self, **fields): return self.intelligence.set_profile(**fields)
    def weak(self, limit=10): return self.intelligence.weak_topics(limit)
    def path(self, subject="", limit=5): return self.adaptive.next_path(subject, limit)
    def questions(self, subject, topic, count=5): return self.adaptive.generate_questions(subject, topic, count)
    def mastery(self, subject, topic): return self.adaptive.mastery(subject, topic)
    def guidance_for(self, strengths, interests=None): return self.guidance.recommend(strengths, interests)

    def handle(self, command: str):
        text = command.strip(); lower = text.lower()
        if lower in {"roadmap", "phase status", "atlas phases"}: return json.dumps(self.status(), indent=2)
        if lower in {"student intelligence", "student profile"}: return json.dumps(self.dashboard(), indent=2)
        if lower.startswith("weak topics"): return json.dumps(self.weak(), indent=2)
        if lower.startswith("adaptive path"):
            subject = text[len("adaptive path"):].strip(); return json.dumps(self.path(subject), indent=2)
        if lower.startswith("mastery "):
            parts = text.split(maxsplit=2)
            if len(parts) == 3 and "/" in parts[2]:
                subject, topic = parts[2].split("/", 1); return str(self.mastery(subject.strip(), topic.strip()))
        if lower == "offline on": return json.dumps(self.lifecycle.set_offline(True))
        if lower == "offline off": return json.dumps(self.lifecycle.set_offline(False))
        if lower == "sync on": return json.dumps(self.lifecycle.set_sync(True))
        if lower == "sync off": return json.dumps(self.lifecycle.set_sync(False))
        return None
