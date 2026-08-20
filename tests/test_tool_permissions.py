from security.tool_permissions import authorize, get_policy


def test_unknown_tools_are_denied():
    assert get_policy("unknown_tool") is None
    assert authorize("unknown_tool") is False


def test_low_risk_tool_is_allowed():
    assert authorize("open_calculator") is True


def test_high_risk_tool_requires_confirmation():
    assert authorize("write_file") is False
    assert authorize("write_file", confirmed=True) is True
