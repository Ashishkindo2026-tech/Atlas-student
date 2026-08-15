from planning.exam_planner import ExamSubject, build_month_plan
from brain.agent import AtlasAgent


def test_multi_subject_month_request_is_detected_before_llm():
    request = "i have 1 month for my half yearly exam and now i have to do 4 chapters in chemistry and 6 chapters in physics and 6 chapters in maths"
    parsed = AtlasAgent._exam_plan_request(request)
    assert parsed is not None
    days, subjects = parsed
    assert days == 30
    assert [(s.name, s.chapters) for s in subjects] == [
        ("Chemistry", 4),
        ("Physics", 6),
        ("Mathematics", 6),
    ]


def test_month_plan_preserves_total_chapter_load():
    result = build_month_plan(30, [ExamSubject("Chemistry", 4), ExamSubject("Physics", 6), ExamSubject("Mathematics", 6)])
    assert "Total chapters: 16" in result
    assert "Chemistry: 4 chapters" in result
    assert "Physics: 6 chapters" in result
    assert "Mathematics: 6 chapters" in result
