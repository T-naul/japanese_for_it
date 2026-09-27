import json
from django.test import TestCase
from apps.content.models import Vocabulary, VocabularyForm, WordType, JLPTLevel, ContentStatus
from apps.content.serializers import VocabularyDetailSerializer


class VocabularyUpdateTestCase(TestCase):
    def test_update_verb_to_adjective_with_empty_forms(self):
        # Create a verb with 1 form
        vocab = Vocabulary.objects.create(
            kanji="緩む",
            hiragana="ゆるむ",
            meaning="Lỏng lẻo",
            word_type=WordType.VERB_1,
            level=JLPTLevel.N2,
            status=ContentStatus.ACCEPTED,
        )
        VocabularyForm.objects.create(vocabulary=vocab, form_type="masu", value="緩みます")

        self.assertEqual(vocab.forms.count(), 1)

        # Update word_type to adjective and pass forms: []
        serializer = VocabularyDetailSerializer(
            instance=vocab,
            data={
                "kanji": "緩い",
                "hiragana": "ゆるい",
                "meaning": "Lỏng; rộng",
                "word_type": "adjective",
                "level": "N2",
                "status": "accepted",
                "forms": [],
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_vocab = serializer.save()

        self.assertEqual(updated_vocab.word_type, "adjective")
        self.assertEqual(updated_vocab.forms.count(), 0)
