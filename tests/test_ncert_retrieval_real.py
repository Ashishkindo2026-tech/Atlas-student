import unittest

from education.document import DocumentChunk, DocumentIndex, tokenize


class NCERTRealRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.index = DocumentIndex()
        self.index.add(DocumentChunk(
            "Newton's third law states that for every action there is an equal and opposite reaction.",
            page=58, chapter="Chapter 9 Force and Laws of Motion", section="9.4 Third Law",
            source="Class 9 Science", class_level=9, subject="Science",
        ))
        self.index.add(DocumentChunk(
            "Electric current is the rate of flow of electric charge through a conductor.",
            page=12, chapter="Electricity", source="Class 10 Science",
            class_level=10, subject="Science",
        ))

    def test_word_level_tokenization_handles_punctuation(self):
        self.assertIn("newton's", tokenize("Newton's law, motion!"))
        self.assertIn("motion", tokenize("Newton's law, motion!"))

    def test_retrieves_relevant_ncert_page(self):
        results = self.index.search("explain Newton third law", limit=1)
        self.assertEqual(results[0].chunk.page, 58)
        self.assertEqual(results[0].chunk.chapter, "Chapter 9 Force and Laws of Motion")

    def test_class_filter_prevents_cross_class_results(self):
        results = self.index.search("science", limit=10, class_level=9, subject="Science")
        self.assertTrue(results)
        self.assertTrue(all(r.chunk.class_level == 9 for r in results))

    def test_subject_filter_is_case_insensitive(self):
        results = self.index.search("electric current", subject="science")
        self.assertEqual(results[0].chunk.class_level, 10)
        self.assertEqual(results[0].chunk.subject, "Science")

    def test_source_metadata_survives_result(self):
        result = self.index.search("opposite reaction", limit=1)[0].chunk
        self.assertEqual(result.source, "Class 9 Science")
        self.assertEqual(result.page, 58)


if __name__ == "__main__":
    unittest.main()
