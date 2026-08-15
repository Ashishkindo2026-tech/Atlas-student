"""Phase 16: opt-in collaboration primitives."""
from dataclasses import dataclass, field

@dataclass
class StudyGroup:
    group_id: str
    members: set[str] = field(default_factory=set)
    shared_notes: list[str] = field(default_factory=list)
    quizzes: list[dict] = field(default_factory=list)
    sharing_enabled: bool = False

    def share(self, member_id: str, item):
        if self.sharing_enabled and member_id in self.members:
            self.shared_notes.append(str(item))
            return True
        return False
