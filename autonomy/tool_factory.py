"""Phase 37: controlled tool creation through the existing extension boundary."""
from dataclasses import dataclass

@dataclass
class ToolProposal:
    name: str
    purpose: str
    files: list[str]
    sandbox_required: bool = True
    approved: bool = False

class ToolFactory:
    def propose(self, name, purpose, files):
        return ToolProposal(name, purpose, list(files))

    def approve(self, proposal):
        proposal.approved=True; return proposal
