import unittest
from education.study_planner import build_study_plan, format_plan


class StudyPlannerTests(unittest.TestCase):
    def test_respects_time_and_prioritizes_low_mastery(self):
        retrieved = [
            {"chapter": "Kinematics", "section": "Motion", "score": 0.8},
            {"chapter": "Laws of Motion", "section": "Force", "score": 0.7},
        ]
        progress = {"concepts": {"Physics::Motion": {"mastery": 30}}}
        blocks = build_study_plan("Physics", 60, retrieved, progress)
        self.assertEqual(sum(b.minutes for b in blocks), 60)
        self.assertEqual(blocks[0].title, "Motion")

    def test_no_material_means_no_invented_plan(self):
        self.assertEqual(build_study_plan("Physics", 120, [], {"concepts": {}}), [])


if __name__ == "__main__":
    unittest.main()
