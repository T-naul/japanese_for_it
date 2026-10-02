from django.test import TestCase
from apps.materials.processing.exceptions import ExtractionValidationError
from apps.materials.processing.validator import ExtractionValidator


class ValidatorTest(TestCase):
    def test_valid_output_accepted(self):
        valid_data = {
            "lesson": {
                "number": 1,
                "title": "Lesson 1",
            },
            "sections": [
                {
                    "title": "Vocab",
                    "type": "vocabulary",
                    "order": 1,
                    "content": "Word list",
                    "data": {},
                    "vocabulary_candidates": [
                        {"surface": "支度", "reading": "したく", "meaning": "preparation"}
                    ],
                },
                {
                    "title": "Grammar",
                    "type": "grammar",
                    "order": 2,
                    "content": "Grammar list",
                    "grammar_candidates": [
                        {"pattern": "～は～です", "meaning": "X is Y"}
                    ],
                },
            ],
        }
        res = ExtractionValidator.validate(valid_data)
        self.assertEqual(res["lesson"]["number"], 1)
        self.assertEqual(len(res["sections"]), 2)

    def test_invalid_section_type_rejected(self):
        data = {
            "lesson": {"number": 1, "title": "Test"},
            "sections": [
                {
                    "title": "Invalid",
                    "type": "unsupported_magic_type",
                    "order": 1,
                }
            ],
        }
        with self.assertRaises(ExtractionValidationError):
            ExtractionValidator.validate(data)

    def test_missing_sections_rejected(self):
        # Missing sections
        with self.assertRaises(ExtractionValidationError):
            ExtractionValidator.validate({"lesson": {"number": 1, "title": "Test"}})

        # Empty sections list
        with self.assertRaises(ExtractionValidationError):
            ExtractionValidator.validate({"lesson": {"number": 1, "title": "Test"}, "sections": []})

    def test_malformed_candidates_rejected(self):
        # Vocabulary candidate missing surface
        bad_vocab = {
            "lesson": {"number": 1, "title": "Test"},
            "sections": [
                {
                    "type": "vocabulary",
                    "order": 1,
                    "vocabulary_candidates": [{"reading": "したく"}],  # missing surface
                }
            ],
        }
        with self.assertRaises(ExtractionValidationError):
            ExtractionValidator.validate(bad_vocab)

        # Grammar candidate missing pattern
        bad_grammar = {
            "lesson": {"number": 1, "title": "Test"},
            "sections": [
                {
                    "type": "grammar",
                    "order": 1,
                    "grammar_candidates": [{"meaning": "X is Y"}],  # missing pattern
                }
            ],
        }
        with self.assertRaises(ExtractionValidationError):
            ExtractionValidator.validate(bad_grammar)
