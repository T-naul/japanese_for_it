from unittest.mock import MagicMock
from django.test import TestCase
from apps.materials.processing.ocr import MIN_TEXT_CHARS, NullOCRProvider, apply_ocr_if_needed
from apps.materials.processing.pdf_parser import ParsedPage


class OCRTest(TestCase):
    def test_ocr_not_called_when_text_sufficient(self):
        page = ParsedPage(
            page_number=1,
            text="This is definitely longer than 10 characters",
            has_text=True,
            metadata={"char_count": 42},
        )
        mock_provider = MagicMock()
        mock_provider.extract_page_text.return_value = "OCR text"

        apply_ocr_if_needed([page], mock_provider)

        mock_provider.extract_page_text.assert_not_called()
        self.assertEqual(page.text, "This is definitely longer than 10 characters")

    def test_ocr_called_when_text_insufficient(self):
        page = ParsedPage(
            page_number=1,
            text="short",  # 5 chars < 10
            has_text=True,
            metadata={"char_count": 5},
        )
        mock_provider = MagicMock()
        mock_provider.extract_page_text.return_value = "Recovered text by OCR"

        apply_ocr_if_needed([page], mock_provider)

        mock_provider.extract_page_text.assert_called_once_with(page)
        self.assertEqual(page.text, "Recovered text by OCR")
        self.assertTrue(page.has_text)
        self.assertTrue(page.metadata.get("ocr_applied"))

    def test_null_ocr_provider_safe(self):
        provider = NullOCRProvider()
        page = ParsedPage(page_number=1, text="", has_text=False)

        res = provider.extract_page_text(page)
        self.assertEqual(res, "")

        pages = apply_ocr_if_needed([page], provider)
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].text, "")
