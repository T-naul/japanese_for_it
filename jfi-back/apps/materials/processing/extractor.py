from abc import ABC, abstractmethod
from .chunker import DocumentChunk, detect_lesson_number


class ContentExtractor(ABC):
    @abstractmethod
    def extract(self, chunk: DocumentChunk) -> dict:
        """
        Extract structured lesson and section content from a DocumentChunk.
        Returns a dictionary conforming to ExtractedDocumentSchema.
        Must NOT write to the database.
        """
        pass


class DummyContentExtractor(ContentExtractor):
    """
    Deterministic extractor for testing and offline development.
    Extracts lesson and candidates from chunk text.
    """

    def extract(self, chunk: DocumentChunk) -> dict:
        lesson_num = chunk.metadata.get("lesson_number")
        if lesson_num is None:
            detected = detect_lesson_number(chunk.text)
            lesson_num = detected if detected is not None else chunk.chunk_index

        text = chunk.text or ""
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        sections = []
        sec_order = 1

        # Text/overview section
        overview_content = lines[0] if lines else f"Lesson {lesson_num} content"
        sections.append({
            "title": f"Lesson {lesson_num} Overview",
            "type": "text",
            "order": sec_order,
            "content": overview_content,
            "data": {},
        })
        sec_order += 1

        # Check for vocabulary candidates
        vocab_candidates = []
        grammar_candidates = []

        for line in lines:
            if "支度" in line or "したく" in line:
                vocab_candidates.append({
                    "surface": "支度",
                    "reading": "したく",
                    "meaning": "preparation",
                })
            elif "学生" in line:
                vocab_candidates.append({
                    "surface": "学生",
                    "reading": "がくせい",
                    "meaning": "student",
                })
            elif "本" in line:
                vocab_candidates.append({
                    "surface": "本",
                    "reading": "ほん",
                    "meaning": "book",
                })

            if "～は～です" in line or "~は~です" in line or "は" in line and "です" in line:
                grammar_candidates.append({
                    "pattern": "～は～です",
                    "meaning": "X is Y",
                })

        if vocab_candidates:
            sections.append({
                "title": "Vocabulary",
                "type": "vocabulary",
                "order": sec_order,
                "content": "Vocabulary section",
                "data": {},
                "vocabulary_candidates": vocab_candidates,
            })
            sec_order += 1

        if grammar_candidates:
            sections.append({
                "title": "Grammar",
                "type": "grammar",
                "order": sec_order,
                "content": "Grammar section",
                "data": {},
                "grammar_candidates": grammar_candidates,
            })
            sec_order += 1

        return {
            "lesson": {
                "number": lesson_num,
                "title": f"第{lesson_num}課",
            },
            "sections": sections,
        }
