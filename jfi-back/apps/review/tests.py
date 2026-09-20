# apps/review/tests.py

from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.content.models import ContentStatus, Grammar, JLPTLevel, Vocabulary, WordType
from apps.review.models import (
    ReviewQuestion,
    ReviewSession,
    ReviewSessionStatus,
)
from apps.review.services import ReviewService
from apps.users.models import UserGrammar, UserVocabulary

User = get_user_model()


class ReviewAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="password123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="password123",
        )

        # Vocabularies
        self.vocabs = []
        for i in range(5):
            v = Vocabulary.objects.create(
                kanji=f"漢字{i}",
                hiragana=f"かんじ{i}",
                meaning=f"Nghĩa từ {i}",
                word_type=WordType.NOUN,
                level=JLPTLevel.N5,
                status=ContentStatus.ACCEPTED,
            )
            self.vocabs.append(v)

        # Grammars
        self.grammars = []
        for i in range(3):
            g = Grammar.objects.create(
                pattern=f"～文法{i}",
                meaning=f"Nghĩa ngữ pháp {i}",
                level=JLPTLevel.N5,
                status=ContentStatus.ACCEPTED,
            )
            self.grammars.append(g)

    def test_1_available_review_with_no_learned_content(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/review/available/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["available"])
        self.assertEqual(response.data["reason"], "NO_LEARNED_CONTENT")
        self.assertEqual(response.data["total"], 0)

    def test_2_available_review_counts_learned_content(self):
        # Learn 2 vocabs and 1 grammar
        UserVocabulary.objects.create(user=self.user1, vocabulary=self.vocabs[0], learned_at=timezone.now())
        UserVocabulary.objects.create(user=self.user1, vocabulary=self.vocabs[1], learned_at=timezone.now())
        UserGrammar.objects.create(user=self.user1, grammar=self.grammars[0], learned_at=timezone.now())

        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/review/available/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["available"])
        self.assertEqual(response.data["vocabulary_count"], 2)
        self.assertEqual(response.data["grammar_count"], 1)
        self.assertEqual(response.data["total"], 3)

    def test_3_create_review_session_and_questions(self):
        # Learn items
        for v in self.vocabs[:3]:
            UserVocabulary.objects.create(user=self.user1, vocabulary=v, learned_at=timezone.now())

        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/review/sessions/", {"limit": 10}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_questions"], 3)
        self.assertEqual(len(response.data["questions"]), 3)

        # Check correct answer is NOT leaked before submission
        q1 = response.data["questions"][0]
        self.assertNotIn("correct_answer", q1)
        self.assertNotIn("is_correct", q1)

    def test_4_limit_validation(self):
        self.client.force_authenticate(user=self.user1)
        response_invalid = self.client.post("/api/review/sessions/", {"limit": 100}, format="json")
        self.assertEqual(response_invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_5_get_session_only_for_owner(self):
        UserVocabulary.objects.create(user=self.user1, vocabulary=self.vocabs[0], learned_at=timezone.now())
        session = ReviewService.create_session(user=self.user1, limit=5)

        # User2 tries to get User1's session
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f"/api/review/sessions/{session.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_6_submit_answers_and_completion(self):
        UserVocabulary.objects.create(user=self.user1, vocabulary=self.vocabs[0], learned_at=timezone.now())
        session = ReviewService.create_session(user=self.user1, limit=5)
        question = session.questions.first()

        self.client.force_authenticate(user=self.user1)

        # Submit correct answer
        correct_answer_val = question.correct_answer.get("choice_id") or question.correct_answer.get("answer_text")
        res_submit = self.client.post(
            f"/api/review/sessions/{session.id}/questions/{question.id}/answer/",
            {"answer": correct_answer_val},
            format="json",
        )
        self.assertEqual(res_submit.status_code, status.HTTP_200_OK)
        self.assertTrue(res_submit.data["is_correct"])
        self.assertTrue(res_submit.data["session_completed"])

        # Try to answer same question again (idempotent / reject)
        res_repeat = self.client.post(
            f"/api/review/sessions/{session.id}/questions/{question.id}/answer/",
            {"answer": correct_answer_val},
            format="json",
        )
        self.assertEqual(res_repeat.status_code, status.HTTP_400_BAD_REQUEST)

    def test_7_session_progress(self):
        UserVocabulary.objects.create(user=self.user1, vocabulary=self.vocabs[0], learned_at=timezone.now())
        session = ReviewService.create_session(user=self.user1, limit=5)

        self.client.force_authenticate(user=self.user1)
        res_progress = self.client.get(f"/api/review/sessions/{session.id}/progress/")
        self.assertEqual(res_progress.status_code, status.HTTP_200_OK)
        self.assertEqual(res_progress.data["total_questions"], 1)
        self.assertEqual(res_progress.data["answered_questions"], 0)

    def test_8_transaction_rollback_on_failure(self):
        UserVocabulary.objects.create(user=self.user1, vocabulary=self.vocabs[0], learned_at=timezone.now())
        with patch.object(ReviewQuestion.objects, "bulk_create", side_effect=RuntimeError("Creation error")):
            with self.assertRaises(RuntimeError):
                ReviewService.create_session(user=self.user1, limit=5)

        self.assertEqual(ReviewSession.objects.count(), 0)
