from django.test import TestCase
from apps.content.models import ContentStatus, Grammar, JLPTLevel, Vocabulary, WordType
from apps.materials.models import LearningMaterial, MaterialLesson, MaterialSection, MaterialType
from apps.materials.processing.matcher import ContentMatcher
from apps.materials.processing.persistence import MaterialPersistenceService


class PersistenceTest(TestCase):
    def setUp(self):
        self.material = LearningMaterial.objects.create(
            title="Japanese for IT Textbook",
            material_type=MaterialType.PDF,
        )
        self.vocab = Vocabulary.objects.create(
            kanji="支度",
            hiragana="したく",
            meaning="preparation",
            word_type=WordType.NOUN,
            level=JLPTLevel.N4,
            status=ContentStatus.ACCEPTED,
        )
        self.grammar = Grammar.objects.create(
            pattern="～は～です",
            meaning="X is Y",
            level=JLPTLevel.N5,
            status=ContentStatus.ACCEPTED,
        )
        self.matcher = ContentMatcher()
        self.service = MaterialPersistenceService(matcher=self.matcher)

        self.extraction_data = {
            "lesson": {
                "number": 1,
                "title": "Lesson 1: Basics",
            },
            "sections": [
                {
                    "title": "Vocabulary Section",
                    "type": "vocabulary",
                    "order": 1,
                    "content": "Vocabulary list",
                    "vocabulary_candidates": [
                        {"surface": "支度", "reading": "したく", "meaning": "prep"}
                    ],
                },
                {
                    "title": "Grammar Section",
                    "type": "grammar",
                    "order": 2,
                    "content": "Grammar list",
                    "grammar_candidates": [
                        {"pattern": "～は～です", "meaning": "X is Y"}
                    ],
                },
            ],
        }

    def test_creates_lesson(self):
        lesson = self.service.persist(self.material, self.extraction_data, page_start=1, page_end=3)

        self.assertEqual(lesson.material, self.material)
        self.assertEqual(lesson.lesson_number, 1)
        self.assertEqual(lesson.title, "Lesson 1: Basics")
        self.assertEqual(lesson.page_start, 1)
        self.assertEqual(lesson.page_end, 3)

    def test_creates_sections(self):
        lesson = self.service.persist(self.material, self.extraction_data, page_start=1, page_end=3)
        sections = MaterialSection.objects.filter(lesson=lesson).order_by("order")

        self.assertEqual(sections.count(), 2)
        self.assertEqual(sections[0].order, 1)
        self.assertEqual(sections[0].section_type, "vocabulary")
        self.assertEqual(sections[1].order, 2)
        self.assertEqual(sections[1].section_type, "grammar")

    def test_links_vocabulary(self):
        lesson = self.service.persist(self.material, self.extraction_data, page_start=1, page_end=3)
        sec = MaterialSection.objects.get(lesson=lesson, order=1)

        self.assertEqual(sec.vocabulary, self.vocab)
        self.assertIn("vocabulary_candidates", sec.data)

    def test_links_grammar(self):
        lesson = self.service.persist(self.material, self.extraction_data, page_start=1, page_end=3)
        sec = MaterialSection.objects.get(lesson=lesson, order=2)

        self.assertEqual(sec.grammar, self.grammar)
        self.assertIn("grammar_candidates", sec.data)

    def test_retry_does_not_duplicate(self):
        # Call persist first time
        self.service.persist(self.material, self.extraction_data, page_start=1, page_end=3)
        initial_lessons_count = MaterialLesson.objects.filter(material=self.material).count()
        initial_sections_count = MaterialSection.objects.filter(lesson__material=self.material).count()

        # Call persist second time with updated title
        updated_data = dict(self.extraction_data)
        updated_data["lesson"] = {"number": 1, "title": "Lesson 1: Updated Title"}
        lesson = self.service.persist(self.material, updated_data, page_start=1, page_end=4)

        # Ensure no duplicates were created
        self.assertEqual(MaterialLesson.objects.filter(material=self.material).count(), initial_lessons_count)
        self.assertEqual(MaterialSection.objects.filter(lesson__material=self.material).count(), initial_sections_count)
        self.assertEqual(lesson.title, "Lesson 1: Updated Title")
        self.assertEqual(lesson.page_end, 4)
