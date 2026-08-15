"""Phases 39-48: bounded context, verification, prediction, federation and resilience primitives."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

@dataclass
class ContextFusion:
    task: str = ""
    history: list = field(default_factory=list)
    available_minutes: int = 0
    deadlines: list = field(default_factory=list)
    environment: dict = field(default_factory=dict)
    previous_attempts: list = field(default_factory=list)
    knowledge_level: float = 0.0
    def build(self): return self.__dict__.copy()

class ReasoningVerifier:
    def verify(self, answer, checks):
        results = [bool(c(answer)) for c in checks]
        return {"passed": all(results), "checks": results, "answer": answer}

class OutcomePredictor:
    def predict(self, outcome_fn, inputs): return outcome_fn(inputs)
    def score(self, predicted, actual):
        return 1.0 if predicted == actual else 0.0

class CapabilityEvolution:
    def propose(self, limitation, architecture_change, protected=False):
        if protected: raise PermissionError("Protected architecture requires human approval")
        return {"limitation": limitation, "change": architecture_change, "approval_required": True}

class Federation:
    def share(self, data, allowed_fields):
        return {k: data[k] for k in allowed_fields if k in data}

class DiscoveryEngine:
    def experiment(self, hypothesis, predicted, observed):
        return {"hypothesis": hypothesis, "predicted": predicted, "observed": observed, "supported": predicted == observed}

class MetaLearning:
    def __init__(self): self.strategies = []
    def record(self, strategy, concept, context, score):
        self.strategies.append({"strategy": strategy, "concept": concept, "context": context, "score": score})
    def best(self, concept=None):
        rows=[x for x in self.strategies if concept is None or x["concept"]==concept]
        return max(rows, key=lambda x:x["score"], default=None)

class CreationEngine:
    STEPS=("research","design","code","test","improve","document","present")
    def plan(self, idea): return {"idea":idea,"steps":list(self.STEPS)}

class RecoveryManager:
    def __init__(self, root="."): self.root=Path(root)
    def quarantine(self, path):
        p=self.root/path; return p.exists()
    def verify(self, checks): return all(bool(c()) for c in checks)

@dataclass
class Constitution:
    automation: str = "approval_required"
    memory_rules: dict = field(default_factory=dict)
    local_data: bool = True
    uncertainty_behavior: str = "stop_and_ask"
    stop_rules: list = field(default_factory=list)
    def validate(self):
        return self.uncertainty_behavior in {"stop_and_ask", "safe_default"}

class ConstitutionStore:
    def __init__(self, path=".atlas/constitution.json"): self.path=Path(path)
    def save(self, constitution):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(constitution.__dict__,indent=2),encoding="utf-8")
    def fingerprint(self):
        if not self.path.exists(): return None
        return hashlib.sha256(self.path.read_bytes()).hexdigest()
