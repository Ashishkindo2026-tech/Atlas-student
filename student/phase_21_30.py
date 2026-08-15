"""Atlas Student phases 21-30: context, reasoning, creation and autonomous study."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class RealTimeContext:
    session: str = ""
    subject: str = ""
    task: str = ""
    minutes_available: int = 0
    deadline: str = ""
    energy: str = ""

class ContextRouter:
    def choose_action(self, context: RealTimeContext) -> str:
        if context.deadline and context.minutes_available <= 30: return "prioritize_deadline"
        if context.energy.lower() in {"low", "tired"}: return "light_revision"
        if context.task: return "work_on_current_task"
        return "review_next_priority"

class SocraticCoach:
    def next_step(self, problem: str, reasoning: str = ""):
        return {"mode":"question_first", "problem":problem, "question":"What do you know already, and what would you try first?", "reasoning":reasoning, "reveal_solution":False}

@dataclass
class ProjectPlan:
    title: str
    requirements: list[str] = field(default_factory=list)
    learning: list[str] = field(default_factory=list)
    design: list[str] = field(default_factory=list)
    build: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    presentation: list[str] = field(default_factory=list)

class ProjectBuilder:
    def create(self, title: str, requirements=(), learning=(), design=(), build=(), test=(), documentation=(), presentation=()):
        return ProjectPlan(title, list(requirements), list(learning), list(design), list(build), list(test), list(documentation), list(presentation))

class CommunicationCoach:
    def practice(self, mode: str, topic: str):
        return {"mode":mode, "topic":topic, "steps":["attempt","feedback","retry","reflection"]}

class DecisionSimulator:
    def compare(self, options):
        return [{"option":o.get("name", ""), "requirements":o.get("requirements", []), "paths":o.get("paths", []), "workload":o.get("workload", "unknown")} for o in options]

class ExplainBack:
    def evaluate(self, explanation: str, evaluator):
        return evaluator(explanation)

@dataclass
class ControlCenter:
    memory_enabled: bool = True
    camera: bool = False
    microphone: bool = False
    files: bool = False
    internet: bool = False
    school_data: bool = False
    automation: bool = False

    def set_permission(self, name: str, value: bool):
        if not hasattr(self, name): raise ValueError(f"Unknown permission: {name}")
        setattr(self, name, bool(value))

class KnowledgeUniverse:
    def search(self, items, query: str):
        q=query.lower(); return [x for x in items if q in str(x).lower()]

class WhyEngine:
    def ask(self, topic: str, answer: str = ""):
        return {"topic":topic,"why_questions":[f"Why does {topic} work?",f"Why is {topic} important?",f"Where is {topic} used?",f"What connects to {topic}?"],"answer_context":answer}

class AutonomousStudy:
    def prepare(self, request: str, minutes: int, analysis: dict):
        return {"request":request,"minutes":minutes,"steps":["analyze_history","identify_weaknesses","create_plan","teach","practice","test","evaluate","revise","report"],"analysis":analysis,"supervision_required":True}

class Atlas30:
    def __init__(self):
        self.context=ContextRouter(); self.socratic=SocraticCoach(); self.projects=ProjectBuilder(); self.communication=CommunicationCoach(); self.decisions=DecisionSimulator(); self.controls=ControlCenter(); self.universe=KnowledgeUniverse(); self.why=WhyEngine(); self.autonomous=AutonomousStudy()
