import unittest

from education.ncert_library import NCERTLibrary


class NCERTLibraryTests(unittest.TestCase):
    def test_core_classes_are_9_to_12(self):
        self.assertEqual(NCERTLibrary.storage_policy()["core_classes"], [9, 10, 11, 12])

    def test_class_validation(self):
        self.assertEqual(NCERTLibrary.validate_class(10), 10)
        with self.assertRaises(ValueError):
            NCERTLibrary.validate_class(8)

    def test_filters_indexed_books(self):
        library = NCERTLibrary([
            {"class": 10, "subject": "Mathematics"},
            {"class": 10, "subject": "Science"},
            {"class": 11, "subject": "Physics"},
        ])
        self.assertEqual(len(library.indexed_books(10)), 2)
        self.assertEqual(library.indexed_books(10, "mathematics")[0]["subject"], "Mathematics")

    def test_missing_core_slots_are_reported_without_inventing_titles(self):
        library = NCERTLibrary([{ "class": 10, "subject": "Mathematics" }])
        missing = library.missing_core({10: ["Mathematics", "Science"]})
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].class_level, 10)
        self.assertEqual(missing[0].subject, "Science")


if __name__ == "__main__":
    unittest.main()
