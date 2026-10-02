from django.test import TestCase
from apps.content.models import ContentStatus, Grammar, JLPTLevel, Vocabulary, WordType
from apps.materials.processing.matcher import ContentMatcher


class MatcherTest(TestCase):
    def setUp(self):
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

    def test_exact_vocabulary_match(self):
        candidate = {"surface": "支度", "reading": "したく", "meaning": "prep"}
        res = self.matcher.match_vocabulary(candidate)

        self.assertIsNotNone(res)
        self.assertEqual(res.matched_id, self.vocab.id)
        self.assertEqual(res.confidence, 1.0)
        self.assertEqual(res.matched_by, "exact_kanji_and_reading")

    def test_reading_match(self):
        # Match kana-only / reading
        candidate = {"surface": "したく", "reading": "したく"}
        res = self.matcher.match_vocabulary(candidate)

        self.assertIsNotNone(res)
        self.assertEqual(res.matched_id, self.vocab.id)
        self.assertTrue(res.confidence >= 0.9)

    def test_no_vocabulary_match_returns_none(self):
        initial_count = Vocabulary.objects.count()
        candidate = {"surface": "不存在単語", "reading": "ふそんざい"}
        res = self.matcher.match_vocabulary(candidate)

        self.assertIsNone(res)
        # Verify no new Vocabulary is created
        self.assertEqual(Vocabulary.objects.count(), initial_count)

    def test_exact_grammar_pattern_match(self):
        candidate = {"pattern": "～は～です", "meaning": "X is Y"}
        res = self.matcher.match_grammar(candidate)

        self.assertIsNotNone(res)
        self.assertEqual(res.matched_id, self.grammar.id)
        self.assertEqual(res.confidence, 1.0)

    def test_no_false_positive(self):
        initial_count = Grammar.objects.count()
        candidate = {"pattern": "～まったく関係ない文法～", "meaning": "unrelated"}
        res = self.matcher.match_grammar(candidate)

        self.assertIsNone(res)
        self.assertEqual(Grammar.objects.count(), initial_count)
