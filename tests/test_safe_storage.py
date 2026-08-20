from pathlib import Path

from core.safe_storage import atomic_write_text, file_lock


def test_atomic_write_text_round_trip(tmp_path):
    path = tmp_path / "state.json"
    atomic_write_text(path, '{"ok": true}')
    assert path.read_text(encoding="utf-8") == '{"ok": true}'
    assert not Path(str(path) + ".tmp").exists()


def test_file_lock_is_reentrant(tmp_path):
    path = tmp_path / "state.json"
    with file_lock(path):
        with file_lock(path):
            atomic_write_text(path, "safe")
    assert path.read_text(encoding="utf-8") == "safe"
