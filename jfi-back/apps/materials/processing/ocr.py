from abc import ABC, abstractmethod

MIN_TEXT_CHARS = 10


class OCRProvider(ABC):
    @abstractmethod
    def extract_page_text(self, page) -> str:
        """Extract text from a page using OCR."""
        pass


class NullOCRProvider(OCRProvider):
    """Default fallback OCR provider that returns empty string without external dependencies."""

    def extract_page_text(self, page) -> str:
        return ""


def apply_ocr_if_needed(pages: list, ocr_provider: OCRProvider | None = None) -> list:
    """
    Applies OCR to pages where extracted text length is below MIN_TEXT_CHARS.
    """
    if not ocr_provider:
        return pages

    for page in pages:
        current_text = getattr(page, "text", "") or ""
        if len(current_text.strip()) < MIN_TEXT_CHARS:
            ocr_text = ocr_provider.extract_page_text(page)
            if ocr_text:
                page.text = ocr_text
                page.has_text = bool(ocr_text.strip())
                if hasattr(page, "metadata") and isinstance(page.metadata, dict):
                    page.metadata["char_count"] = len(ocr_text)
                    page.metadata["has_text"] = page.has_text
                    page.metadata["ocr_applied"] = True

    return pages
