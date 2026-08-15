"""Phase 35: dependency-aware goal decomposition."""
from dataclasses import dataclass, field

@dataclass
class Task:
    id: str
    title: str
    dependencies: set[str] = field(default_factory=set)
    completed: bool = False

class GoalDecomposer:
    def decompose(self, goal, steps):
        tasks=[]
        for i, title in enumerate(steps):
            tasks.append(Task(f"task-{i+1}", title, {f"task-{i}"} if i else set()))
        return tasks

    def ready(self, tasks):
        done={t.id for t in tasks if t.completed}
        return [t for t in tasks if not t.completed and t.dependencies <= done]
