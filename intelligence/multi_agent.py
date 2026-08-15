"""Phase 19: one-user-facing Atlas over specialized agents."""
from dataclasses import dataclass

@dataclass
class AgentResult:
    agent: str
    result: object

class MultiAgentAtlas:
    def __init__(self, agents: dict[str, object]):
        self.agents = agents

    def dispatch(self, role: str, task):
        agent = self.agents.get(role)
        if agent is None:
            raise KeyError(f"Unknown Atlas agent: {role}")
        handler = getattr(agent, "run", agent)
        return AgentResult(role, handler(task))
