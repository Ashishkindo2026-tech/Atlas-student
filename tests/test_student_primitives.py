from pathlib import Path

from brain.context_builder import build_context
from brain.homework_mode import HomeworkMode
from brain.progress import Progress
from Study.book_manager import BookManager


def test_context_is_bounded_and_structured():
    result = build_context(
        "current",
        [{"role": "user", "content": "old"}, {"role": "assistant", "content": "new"}],
        ["remembered"],
        max_history=1,
        max_memories=1,
    )
    assert "current" in result
    assert "new" in result
    assert "old" not in result
    assert "remembered" in result


def test_homework_mode_advances():
    mode = HomeworkMode(subject="Physics")
    assert mode.next_step().step == 2
    assert "Physics" in mode.instruction("Explain velocity")


def test_progress_round_trip():
    progress = Progress()
    progress.mark_complete("Motion")
    restored = Progress.from_dict(progress.to_dict())
    assert restored.is_complete("Motion")
    assert restored.completion_ratio(2) == 0.5


def test_book_manager_round_trip(tmp_path: Path):
    manager = BookManager(tmp_path / "books.json")
    manager.add("Physics NCERT", "Physics")
    manager.save()
    restored = BookManager(tmp_path / "books.json")
    assert [book.title for book in restored.search("physics")] == ["Physics NCERT"]
    assert restored.remove("Physics NCERT")
