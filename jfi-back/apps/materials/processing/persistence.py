from django.db import transaction
from apps.materials.models import LearningMaterial, MaterialLesson, MaterialSection, MaterialSectionType
from .matcher import ContentMatcher


class MaterialPersistenceService:
    def __init__(self, matcher: ContentMatcher | None = None):
        self.matcher = matcher or ContentMatcher()

    def persist(
        self,
        material: LearningMaterial,
        extraction_data: dict,
        page_start: int | None = None,
        page_end: int | None = None,
    ) -> MaterialLesson:
        lesson_data = extraction_data["lesson"]
        lesson_number = lesson_data["number"]
        lesson_title = lesson_data.get("title", f"Lesson {lesson_number}")
        sections_data = extraction_data.get("sections", [])

        with transaction.atomic():
            # 1. Create or update MaterialLesson
            lesson, _ = MaterialLesson.objects.update_or_create(
                material=material,
                lesson_number=lesson_number,
                defaults={
                    "title": lesson_title,
                    "page_start": page_start,
                    "page_end": page_end,
                    "metadata": {
                        "source": {
                            "page_start": page_start,
                            "page_end": page_end,
                        },
                        "total_sections": len(sections_data),
                    },
                },
            )

            # 2. Create or update MaterialSections
            for sec_data in sections_data:
                order = sec_data["order"]
                section_type = sec_data.get("type", MaterialSectionType.TEXT)
                title = sec_data.get("title", "")
                content = sec_data.get("content", "")
                data = dict(sec_data.get("data", {}))

                vocab_candidates = sec_data.get("vocabulary_candidates") or []
                grammar_candidates = sec_data.get("grammar_candidates") or []

                if vocab_candidates:
                    data["vocabulary_candidates"] = vocab_candidates
                if grammar_candidates:
                    data["grammar_candidates"] = grammar_candidates

                # Attempt matching
                matched_vocab_id = None
                for cand in vocab_candidates:
                    res = self.matcher.match_vocabulary(cand)
                    if res:
                        matched_vocab_id = res.matched_id
                        break

                matched_grammar_id = None
                for g_cand in grammar_candidates:
                    res = self.matcher.match_grammar(g_cand)
                    if res:
                        matched_grammar_id = res.matched_id
                        break

                MaterialSection.objects.update_or_create(
                    lesson=lesson,
                    order=order,
                    defaults={
                        "title": title,
                        "section_type": section_type,
                        "content": content,
                        "page_start": page_start,
                        "page_end": page_end,
                        "data": data,
                        "vocabulary_id": matched_vocab_id,
                        "grammar_id": matched_grammar_id,
                    },
                )

        return lesson
