from unittest.mock import MagicMock
from django.test import TestCase
from apps.materials.processing.chunker import DocumentChunk
from apps.materials.processing.extractor import DummyContentExtractor


class ExtractorTest(TestCase):
    def test_dummy_extractor_valid_structure(self):
        chunk = DocumentChunk(
            chunk_index=1,
            page_start=1,
            page_end=2,
            text="第1課\n支度\nしたく\n学生\n～は～です",
            metadata={"lesson_number": 1},
        )
        extractor = DummyContentExtractor()
        data = extractor.extract(chunk)

        self.assertIn("lesson", data)
        self.assertEqual(data["lesson"]["number"], 1)
        self.assertIn("sections", data)
        self.assertTrue(len(data["sections"]) > 0)

        # Check section types
        sec_types = [s["type"] for s in data["sections"]]
        self.assertIn("text", sec_types)
        self.assertIn("vocabulary", sec_types)
        self.assertIn("grammar", sec_types)

    def test_extractor_exception_propagates(self):
        chunk = DocumentChunk(
            chunk_index=1,
            page_start=1,
            page_end=1,
            text="Error test",
        )
        mock_extractor = MagicMock()
        mock_extractor.extract.side_effect = RuntimeError("Extraction provider failed")

        with self.assertRaises(RuntimeError) as ctx:
            mock_extractor.extract(chunk)

        self.assertIn("Extraction provider failed", str(ctx.exception))
