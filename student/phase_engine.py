"""Unified facade for Atlas Student development phases 1-30."""
from __future__ import annotations
import json
from brain.student_intelligence import StudentIntelligence, AdaptiveLearning
from guidance.career import GuidanceEngine
from student.lifecycle import AtlasLifecycle
from student.advanced_intelligence import AdvancedStudentSystem
from student.phase_21_30 import Atlas30, RealTimeContext

class PhaseEngine:
    def __init__(self):
        self.intelligence = StudentIntelligence(); self.adaptive = AdaptiveLearning(self.intelligence)
        self.guidance = GuidanceEngine(); self.lifecycle = AtlasLifecycle(); self.advanced = AdvancedStudentSystem(); self.p30 = Atlas30()
    def status(self): return self.lifecycle.status()
    def dashboard(self): return {"lifecycle": self.lifecycle.status(), "intelligence": self.intelligence.data(), "adaptive_path": self.adaptive.next_path()}
    def attempt(self, subject, topic, correct, difficulty=1): return self.intelligence.record_attempt(subject, topic, correct, difficulty)
    def mistake(self, subject, topic, error, correction=""): return self.intelligence.record_mistake(subject, topic, error, correction)
    def goal(self, goal, deadline="", target=""): return self.intelligence.set_goal(goal, deadline, target)
    def profile(self, **fields): return self.intelligence.set_profile(**fields)
    def weak(self, limit=10): return self.intelligence.weak_topics(limit)
    def path(self, subject="", limit=5): return self.adaptive.next_path(subject, limit)
    def questions(self, subject, topic, count=5): return self.adaptive.generate_questions(subject, topic, count)
    def mastery(self, subject, topic): return self.adaptive.mastery(subject, topic)
    def guidance_for(self, strengths, interests=None): return self.guidance.recommend(strengths, interests)
    def advanced_analysis(self, attempts, topics=(), goals=()): return self.advanced.analyze(attempts, topics, goals)
    def study_session(self, minutes, focus, recommendations=()): return self.advanced.autonomous.session(minutes, focus, recommendations)
    def digital_twin(self, attempts, mistakes, goals, interests=()): return self.advanced.digital_twin.build(attempts, mistakes, goals, interests)
    def continuity_export(self, memory, achievements=(), projects=(), learning_history=(), preferences=None): return self.advanced.continuity.export(memory, achievements, projects, learning_history, preferences or {})
    def realtime_action(self, **kwargs): return self.p30.context.choose_action(RealTimeContext(**kwargs))
    def socratic(self, problem, reasoning=""): return self.p30.socratic.next_step(problem, reasoning)
    def project(self, title, **kwargs): return self.p30.projects.create(title, **kwargs)
    def communication(self, mode, topic): return self.p30.communication.practice(mode, topic)
    def decision(self, options): return self.p30.decisions.compare(options)
    def explain_back(self, explanation, evaluator): return self.p30.explain_back.evaluate(explanation, evaluator)
    def knowledge_search(self, items, query): return self.p30.universe.search(items, query)
    def why(self, topic, answer=""): return self.p30.why.ask(topic, answer)
    def autonomous_prepare(self, request, minutes, analysis): return self.p30.autonomous.prepare(request, minutes, analysis)
    def set_permission(self, name, value): return self.p30.controls.set_permission(name, value)
    def handle(self, command: str):
        text = command.strip(); lower = text.lower()
        if lower in {"roadmap", "phase status", "atlas phases"}: return json.dumps(self.status(), indent=2)
        if lower in {"student intelligence", "student profile"}: return json.dumps(self.dashboard(), indent=2)
        if lower.startswith("weak topics"): return json.dumps(self.weak(), indent=2)
        if lower.startswith("adaptive path"):
            subject = text[len("adaptive path"):].strip(); return json.dumps(self.path(subject), indent=2)
        if lower == "socratic": return json.dumps(self.socratic("current problem"), indent=2)
        if lower == "why": return json.dumps(self.why("current concept"), indent=2)
        if lower == "offline on": return json.dumps(self.lifecycle.set_offline(True))
        if lower == "offline off": return json.dumps(self.lifecycle.set_offline(False))
        if lower == "sync on": return json.dumps(self.lifecycle.set_sync(True))
        if lower == "sync off": return json.dumps(self.lifecycle.set_sync(False))
        return None
