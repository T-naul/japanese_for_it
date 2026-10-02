from dataclasses import dataclass, field
import re
from .pdf_parser import ParsedPage

FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")

LESSON_PATTERNS = [
    re.compile(r"第\s*([0-9０-９]+)\s*課"),
    re.compile(r"Lesson\s*([0-9]+)", re.IGNORECASE),
]


@dataclass
class DocumentChunk:
    chunk_index: int
    page_start: int
    page_end: int
    text: str
    metadata: dict = field(default_factory=dict)


def detect_lesson_number(text: str) -> int | None:
    for pattern in LESSON_PATTERNS:
        match = pattern.search(text)
        if match:
            raw_digit = match.group(1).translate(FULLWIDTH_DIGITS)
            try:
                return int(raw_digit)
            except ValueError:
                pass
    return None


class DocumentChunker:
    def __init__(self, max_chars: int = 12000):
        self.max_chars = max_chars

    def chunk(self, pages: list[ParsedPage]) -> list[DocumentChunk]:
        if not pages:
            return []

        # Step 1: Detect lesson boundaries
        lesson_page_indices = []
        last_lesson_num = None
        for i, page in enumerate(pages):
            lesson_num = detect_lesson_number(page.text)
            if lesson_num is not None:
                if last_lesson_num is None or lesson_num != last_lesson_num:
                    lesson_page_indices.append((i, lesson_num))
                    last_lesson_num = lesson_num


        if lesson_page_indices:
            return self._chunk_by_detected_lessons(pages, lesson_page_indices)
        else:
            return self._chunk_by_page_groups(pages)

    def _chunk_by_detected_lessons(
        self, pages: list[ParsedPage], lesson_page_indices: list[tuple[int, int]]
    ) -> list[DocumentChunk]:
        chunks = []
        num_markers = len(lesson_page_indices)

        for marker_idx in range(num_markers):
            start_page_idx, lesson_num = lesson_page_indices[marker_idx]
            if marker_idx + 1 < num_markers:
                end_page_idx = lesson_page_indices[marker_idx + 1][0] - 1
            else:
                end_page_idx = len(pages) - 1

            # Edge case: if start_page_idx > end_page_idx (two markers on same page)
            if end_page_idx < start_page_idx:
                end_page_idx = start_page_idx

            lesson_pages = pages[start_page_idx : end_page_idx + 1]
            chunk_text = "\n\n".join(p.text for p in lesson_pages if p.text)
            page_start = lesson_pages[0].page_number
            page_end = lesson_pages[-1].page_number

            chunks.append(
                DocumentChunk(
                    chunk_index=len(chunks) + 1,
                    page_start=page_start,
                    page_end=page_end,
                    text=chunk_text,
                    metadata={
                        "lesson_number": lesson_num,
                        "strategy": "lesson_heading",
                        "total_pages": len(lesson_pages),
                    },
                )
            )

        return chunks

    def _chunk_by_page_groups(self, pages: list[ParsedPage]) -> list[DocumentChunk]:
        chunks = []
        current_pages = []
        current_chars = 0

        for page in pages:
            page_len = len(page.text or "")
            if current_pages and (current_chars + page_len > self.max_chars):
                # Finalize current chunk
                chunk_text = "\n\n".join(p.text for p in current_pages if p.text)
                chunks.append(
                    DocumentChunk(
                        chunk_index=len(chunks) + 1,
                        page_start=current_pages[0].page_number,
                        page_end=current_pages[-1].page_number,
                        text=chunk_text,
                        metadata={
                            "strategy": "fallback_page_group",
                            "total_pages": len(current_pages),
                        },
                    )
                )
                current_pages = [page]
                current_chars = page_len
            else:
                current_pages.append(page)
                current_chars += page_len

        if current_pages:
            chunk_text = "\n\n".join(p.text for p in current_pages if p.text)
            chunks.append(
                DocumentChunk(
                    chunk_index=len(chunks) + 1,
                    page_start=current_pages[0].page_number,
                    page_end=current_pages[-1].page_number,
                    text=chunk_text,
                    metadata={
                        "strategy": "fallback_page_group",
                        "total_pages": len(current_pages),
                    },
                )
            )

        return chunks
