"""Phase 13: personal knowledge network primitives."""
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class KnowledgeNode:
    id: str
    label: str
    subject: str | None = None
    mastery: float = 0.0
    tags: set[str] = field(default_factory=set)

class KnowledgeNetwork:
    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.edges: dict[str, set[tuple[str, str]]] = defaultdict(set)

    def add_concept(self, node: KnowledgeNode):
        self.nodes[node.id] = node

    def connect(self, source: str, target: str, relation: str = "related"):
        if source in self.nodes and target in self.nodes:
            self.edges[source].add((target, relation))

    def prerequisites(self, concept: str):
        return [n for n, links in self.edges.items() if any(t == concept and r == "prerequisite" for t, r in links)]

    def gaps(self, threshold: float = 0.6):
        return [n for n in self.nodes.values() if n.mastery < threshold]

    def related(self, concept: str):
        return [self.nodes[t] for t, _ in self.edges.get(concept, set()) if t in self.nodes]
