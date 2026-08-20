"""Central tool-permission policy for Atlas.

The policy is deliberately conservative: tools must be explicitly registered
and callers must request a named capability before execution.
"""
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ToolPolicy:
    name: str
    risk: RiskLevel
    requires_confirmation: bool = False


POLICIES = {
    "open_notepad": ToolPolicy("open_notepad", RiskLevel.LOW),
    "open_calculator": ToolPolicy("open_calculator", RiskLevel.LOW),
    "open_paint": ToolPolicy("open_paint", RiskLevel.LOW),
    "read_file": ToolPolicy("read_file", RiskLevel.MEDIUM, True),
    "write_file": ToolPolicy("write_file", RiskLevel.HIGH, True),
    "run_command": ToolPolicy("run_command", RiskLevel.HIGH, True),
}


def get_policy(tool_name: str) -> ToolPolicy | None:
    return POLICIES.get(str(tool_name).strip())


def authorize(tool_name: str, confirmed: bool = False) -> bool:
    """Return whether a tool invocation is permitted by policy."""
    policy = get_policy(tool_name)
    if policy is None:
        return False
    if policy.requires_confirmation and not confirmed:
        return False
    return True
