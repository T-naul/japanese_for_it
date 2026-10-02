import os
import tempfile
from django.test import TestCase
from apps.materials.processing.exceptions import PDFProcessingError
from apps.materials.processing.pdf_parser import PDFParser
from .fixtures import MockFitzLib, write_synthetic_pdf_file


class PDFParserTest(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.valid_pdf_path = os.path.join(self.temp_dir.name, "valid.pdf")
        self.empty_pdf_path = os.path.join(self.temp_dir.name, "empty.pdf")
        self.invalid_file_path = os.path.join(self.temp_dir.name, "not_a_pdf.txt")

        # Write synthetic PDFs
        write_synthetic_pdf_file(["Page 1 content", "Page 2 content"], self.valid_pdf_path)
        write_synthetic_pdf_file(["", "Page 2 with text"], self.empty_pdf_path)

        with open(self.invalid_file_path, "w") as f:
            f.write("This is definitely not a PDF")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_pdf(self):
        parser = PDFParser()
        pages = parser.parse(self.valid_pdf_path)
        self.assertEqual(len(pages), 2)
        self.assertTrue(all(p.has_text for p in pages))

    def test_page_number_starts_at_1(self):
        parser = PDFParser()
        pages = parser.parse(self.valid_pdf_path)
        self.assertEqual(pages[0].page_number, 1)
        self.assertEqual(pages[1].page_number, 2)

    def test_text_extraction(self):
        parser = PDFParser()
        pages = parser.parse(self.valid_pdf_path)
        self.assertIn("Page 1 content", pages[0].text)
        self.assertIn("Page 2 content", pages[1].text)
        self.assertEqual(pages[0].metadata["char_count"], len(pages[0].text))

    def test_empty_page(self):
        parser = PDFParser()
        pages = parser.parse(self.empty_pdf_path)
        self.assertEqual(len(pages), 2)
        self.assertFalse(pages[0].has_text)
        self.assertEqual(pages[0].text.strip(), "")
        self.assertTrue(pages[1].has_text)

    def test_invalid_pdf_raises_expected_exception(self):
        parser = PDFParser()
        # Non-existent file
        with self.assertRaises(PDFProcessingError):
            parser.parse(os.path.join(self.temp_dir.name, "does_not_exist.pdf"))

        # Invalid PDF header
        with self.assertRaises(PDFProcessingError):
            parser.parse(self.invalid_file_path)

    def test_pymupdf_fitz_integration(self):
        mock_fitz = MockFitzLib(pages_text=["Fitz page 1", "Fitz page 2"])
        parser = PDFParser(fitz_lib=mock_fitz)
        pages = parser.parse(self.valid_pdf_path)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].page_number, 1)
        self.assertEqual(pages[0].text, "Fitz page 1")
        self.assertEqual(pages[0].width, 595.0)
        self.assertEqual(pages[0].height, 842.0)
