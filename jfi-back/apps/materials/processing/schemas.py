from typing import Any, TypedDict
from apps.materials.models import MaterialSectionType

VALID_SECTION_TYPES = {choice[0] for choice in MaterialSectionType.choices}


class VocabularyCandidate(TypedDict, total=False):
    surface: str
    reading: str
    meaning: str


class GrammarCandidate(TypedDict, total=False):
    pattern: str
    meaning: str


class SectionSchema(TypedDict, total=False):
    title: str
    type: str
    order: int
    content: str
    data: dict[str, Any]
    vocabulary_candidates: list[VocabularyCandidate]
    grammar_candidates: list[GrammarCandidate]


class LessonSchema(TypedDict):
    number: int
    title: str


class ExtractedDocumentSchema(TypedDict):
    lesson: LessonSchema
    sections: list[SectionSchema]
