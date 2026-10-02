from django.test import TestCase
from apps.materials.processing.chunker import DocumentChunker
from apps.materials.processing.pdf_parser import ParsedPage


class ChunkerTest(TestCase):
    def test_detect_dai_1_ka(self):
        pages = [
            ParsedPage(page_number=1, text="第1課\nこんにちは\n学生", has_text=True),
            ParsedPage(page_number=2, text="私は学生です。", has_text=True),
            ParsedPage(page_number=3, text="第2課\n本\n読みます", has_text=True),
        ]
        chunker = DocumentChunker()
        chunks = chunker.chunk(pages)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata["lesson_number"], 1)
        self.assertEqual(chunks[0].page_start, 1)
        self.assertEqual(chunks[0].page_end, 2)
        self.assertIn("第1課", chunks[0].text)

        self.assertEqual(chunks[1].metadata["lesson_number"], 2)
        self.assertEqual(chunks[1].page_start, 3)
        self.assertEqual(chunks[1].page_end, 3)
        self.assertIn("第2課", chunks[1].text)

    def test_detect_dai_fullwidth_1_ka(self):
        pages = [
            ParsedPage(page_number=1, text="第１課\n日本の会社", has_text=True),
            ParsedPage(page_number=2, text="第２課\n会議", has_text=True),
        ]
        chunker = DocumentChunker()
        chunks = chunker.chunk(pages)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].metadata["lesson_number"], 1)
        self.assertEqual(chunks[1].metadata["lesson_number"], 2)

    def test_detect_lesson_1(self):
        pages = [
            ParsedPage(page_number=1, text="Lesson 1: Introduction", has_text=True),
            ParsedPage(page_number=2, text="Lesson 02: Vocabulary", has_text=True),
            ParsedPage(page_number=3, text="LESSON 3: Grammar", has_text=True),
        ]
        chunker = DocumentChunker()
        chunks = chunker.chunk(pages)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].metadata["lesson_number"], 1)
        self.assertEqual(chunks[1].metadata["lesson_number"], 2)
        self.assertEqual(chunks[2].metadata["lesson_number"], 3)

    def test_fallback_page_chunking(self):
        # Text without any lesson headings
        pages = [
            ParsedPage(page_number=1, text="General Japanese text page 1", has_text=True),
            ParsedPage(page_number=2, text="General Japanese text page 2", has_text=True),
            ParsedPage(page_number=3, text="General Japanese text page 3", has_text=True),
        ]
        chunker = DocumentChunker(max_chars=100)
        chunks = chunker.chunk(pages)

        self.assertTrue(len(chunks) >= 1)
        self.assertEqual(chunks[0].metadata["strategy"], "fallback_page_group")

    def test_max_chunk_size_approximately_respected(self):
        # Create 10 pages with 100 characters each, max_chars = 250 -> roughly 2-3 pages per chunk
        pages = [
            ParsedPage(page_number=i, text="x" * 100, has_text=True)
            for i in range(1, 11)
        ]
        chunker = DocumentChunker(max_chars=250)
        chunks = chunker.chunk(pages)

        for c in chunks:
            # Each chunk should contain pages without exceeding the limit unless a single page exceeds it
            self.assertTrue(len(c.text) <= 350)
        self.assertTrue(len(chunks) >= 4)

    def test_page_ranges_correct(self):
        pages = [
            ParsedPage(page_number=1, text="第1課 start", has_text=True),
            ParsedPage(page_number=2, text="middle page", has_text=True),
            ParsedPage(page_number=3, text="end of lesson 1", has_text=True),
            ParsedPage(page_number=4, text="第2課 start", has_text=True),
        ]
        chunker = DocumentChunker()
        chunks = chunker.chunk(pages)

        self.assertEqual(chunks[0].page_start, 1)
        self.assertEqual(chunks[0].page_end, 3)
        self.assertEqual(chunks[1].page_start, 4)
        self.assertEqual(chunks[1].page_end, 4)
