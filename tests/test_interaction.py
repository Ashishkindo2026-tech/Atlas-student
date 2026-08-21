from interaction.multimodal import InputPacket
from voice.wake_word import WakeWord


def test_wake_word_extracts_command():
    matched, command = WakeWord().accept("Hey Atlas explain Newton's laws")
    assert matched
    assert command == "explain Newton's laws"


def test_wake_word_rejects_unrelated_speech():
    matched, command = WakeWord().accept("hello there")
    assert not matched
    assert command == ""


def test_multimodal_requires_input():
    packet = InputPacket()
    try:
        packet.validate()
    except ValueError:
        return
    raise AssertionError("empty input packet must be rejected")
