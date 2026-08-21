from atlas_core.quality_gate import evaluate_phase
from distribution.hardware import recommend_profile
from privacy.policy import DEFAULT_POLICY


def test_phase_a_gate_requires_all_evidence():
    result = evaluate_phase("A", ["architecture"])
    assert result.score == 2.5
    assert not result.passed
    assert "configuration" in result.missing


def test_privacy_defaults_to_local_first():
    assert DEFAULT_POLICY.local_only is True
    assert DEFAULT_POLICY.allow_network_llm is False


def test_hardware_profiles_are_conservative():
    assert recommend_profile(4) == "low-end"
    assert recommend_profile(8) == "balanced"
    assert recommend_profile(16) == "high-memory"
