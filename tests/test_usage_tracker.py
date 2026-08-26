from datetime import datetime, timedelta, timezone

from gui import usage_tracker


def test_customization_offer_after_seven_days(tmp_path, monkeypatch):
    monkeypatch.setattr(usage_tracker, "APPDATA", tmp_path)
    monkeypatch.setattr(usage_tracker, "USAGE_FILE", tmp_path / "usage.json")
    first = datetime(2026, 8, 1, tzinfo=timezone.utc)

    usage_tracker.record_launch(first)
    assert usage_tracker.days_used(first + timedelta(days=6, hours=23)) == 6
    assert not usage_tracker.should_offer_customization(first + timedelta(days=6, hours=23))
    assert usage_tracker.should_offer_customization(first + timedelta(days=7))


def test_offer_is_one_time(tmp_path, monkeypatch):
    monkeypatch.setattr(usage_tracker, "APPDATA", tmp_path)
    monkeypatch.setattr(usage_tracker, "USAGE_FILE", tmp_path / "usage.json")
    first = datetime(2026, 8, 1, tzinfo=timezone.utc)

    usage_tracker.record_launch(first)
    assert usage_tracker.should_offer_customization(first + timedelta(days=7))
    usage_tracker.mark_offer_shown()
    assert not usage_tracker.should_offer_customization(first + timedelta(days=8))
