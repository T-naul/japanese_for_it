from .exceptions import ExtractionValidationError
from .schemas import VALID_SECTION_TYPES


class ExtractionValidator:
    @staticmethod
    def validate(data: dict) -> dict:
        if not isinstance(data, dict):
            raise ExtractionValidationError("Extracted data must be a dictionary.")

        # 1. Validate lesson
        if "lesson" not in data or not isinstance(data["lesson"], dict):
            raise ExtractionValidationError("Field 'lesson' is required and must be a dictionary.")

        lesson = data["lesson"]
        if "number" not in lesson:
            raise ExtractionValidationError("Field 'lesson.number' is required.")
        if not isinstance(lesson["number"], int) or lesson["number"] <= 0:
            raise ExtractionValidationError("Field 'lesson.number' must be a positive integer.")

        lesson_title = lesson.get("title", "")
        if not isinstance(lesson_title, str):
            raise ExtractionValidationError("Field 'lesson.title' must be a string.")

        # 2. Validate sections
        if "sections" not in data or not isinstance(data["sections"], list):
            raise ExtractionValidationError("Field 'sections' is required and must be a list.")
        if len(data["sections"]) == 0:
            raise ExtractionValidationError("Field 'sections' cannot be empty.")

        validated_sections = []
        for idx, section in enumerate(data["sections"]):
            if not isinstance(section, dict):
                raise ExtractionValidationError(f"Section at index {idx} must be a dictionary.")

            # Section type
            section_type = section.get("type")
            if not section_type or section_type not in VALID_SECTION_TYPES:
                raise ExtractionValidationError(
                    f"Section at index {idx} has invalid type '{section_type}'. Valid types: {sorted(VALID_SECTION_TYPES)}"
                )

            # Order
            order = section.get("order")
            if order is None or not isinstance(order, int) or order <= 0:
                raise ExtractionValidationError(f"Section at index {idx} must have positive integer 'order'.")

            # Title & content
            title = section.get("title", "")
            if title is not None and not isinstance(title, str):
                raise ExtractionValidationError(f"Section at index {idx} 'title' must be a string.")

            content = section.get("content", "")
            if content is not None and not isinstance(content, str):
                raise ExtractionValidationError(f"Section at index {idx} 'content' must be a string.")

            # Data dict
            sec_data = section.get("data", {})
            if not isinstance(sec_data, dict):
                raise ExtractionValidationError(f"Section at index {idx} 'data' must be a dictionary.")

            # Vocabulary candidates
            vocab_candidates = section.get("vocabulary_candidates")
            if vocab_candidates is not None:
                if not isinstance(vocab_candidates, list):
                    raise ExtractionValidationError(f"Section at index {idx} 'vocabulary_candidates' must be a list.")
                for c_idx, cand in enumerate(vocab_candidates):
                    if not isinstance(cand, dict):
                        raise ExtractionValidationError(
                            f"Section {idx} vocabulary candidate {c_idx} must be a dictionary."
                        )
                    surface = cand.get("surface")
                    if not surface or not isinstance(surface, str) or not surface.strip():
                        raise ExtractionValidationError(
                            f"Section {idx} vocabulary candidate {c_idx} must have non-empty string 'surface'."
                        )

            # Grammar candidates
            grammar_candidates = section.get("grammar_candidates")
            if grammar_candidates is not None:
                if not isinstance(grammar_candidates, list):
                    raise ExtractionValidationError(f"Section at index {idx} 'grammar_candidates' must be a list.")
                for g_idx, g_cand in enumerate(grammar_candidates):
                    if not isinstance(g_cand, dict):
                        raise ExtractionValidationError(
                            f"Section {idx} grammar candidate {g_idx} must be a dictionary."
                        )
                    pattern = g_cand.get("pattern")
                    if not pattern or not isinstance(pattern, str) or not pattern.strip():
                        raise ExtractionValidationError(
                            f"Section {idx} grammar candidate {g_idx} must have non-empty string 'pattern'."
                        )

            validated_sections.append(section)

        return {
            "lesson": {
                "number": lesson["number"],
                "title": lesson_title.strip() if lesson_title else f"Lesson {lesson['number']}",
            },
            "sections": validated_sections,
        }
