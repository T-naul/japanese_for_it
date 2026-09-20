# apps/learning/tests.py

from datetime import date
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.content.models import ContentStatus, Grammar, JLPTLevel, Vocabulary, WordType
from apps.learning.models import (
    DayGrammar,
    DayVocabulary,
    StudyPlan,
    StudyPlanDay,
    StudyPlanStatus,
)
from apps.learning.services import StudyPlanService
from apps.users.models import UserGrammar, UserVocabulary

User = get_user_model()


class LearningAPITestCase(TestCase):

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

        # Create 10 accepted Vocabularies for N5
        self.vocabs = []
        for i in range(10):
            v = Vocabulary.objects.create(
                kanji=f"漢字{i}",
                hiragana=f"かんじ{i}",
                meaning=f"Meaning {i}",
                word_type=WordType.NOUN,
                level=JLPTLevel.N5,
                status=ContentStatus.ACCEPTED,
            )
            self.vocabs.append(v)

        # Create 5 accepted Grammars for N5
        self.grammars = []
        for i in range(5):
            g = Grammar.objects.create(
                pattern=f"～パターン{i}",
                meaning=f"Meaning {i}",
                level=JLPTLevel.N5,
                status=ContentStatus.ACCEPTED,
            )
            self.grammars.append(g)

    def test_create_study_plan_success(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            "/api/learning/plans/",
            {
                "level": "N5",
                "total_days": 5,
                "start_date": "2026-09-21",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["level"], "N5")
        self.assertEqual(response.data["total_days"], 5)
        self.assertEqual(response.data["status"], "active")

        # Verify plan in DB
        plan = StudyPlan.objects.get(id=response.data["id"])
        self.assertEqual(plan.user, self.user1)
        self.assertEqual(plan.days.count(), 5)

        # Verify distribution (10 vocabs / 5 days = 2 each; 5 grammars / 5 days = 1 each)
        for day in plan.days.all():
            self.assertEqual(day.vocabularies.count(), 2)
            self.assertEqual(day.grammars.count(), 1)

    def test_cannot_create_second_active_plan(self):
        self.client.force_authenticate(user=self.user1)

        # Create first plan
        self.client.post(
            "/api/learning/plans/",
            {"level": "N5", "total_days": 5},
            format="json",
        )

        # Attempt to create second active plan
        response = self.client.post(
            "/api/learning/plans/",
            {"level": "N5", "total_days": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_user_cannot_access_other_users_plan(self):
        # Create plan for user1
        plan1 = StudyPlanService.create_plan(user=self.user1, level=JLPTLevel.N5, total_days=5)

        # Authenticate as user2
        self.client.force_authenticate(user=self.user2)

        # Get plan1 detail
        response = self.client.get(f"/api/learning/plans/{plan1.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # List plans
        response = self.client.get("/api/learning/plans/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        # Get days list of plan1
        response = self.client.get(f"/api/learning/plans/{plan1.id}/days/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_day_detail_and_no_carryover(self):
        plan = StudyPlanService.create_plan(user=self.user1, level=JLPTLevel.N5, total_days=5)
        day1 = plan.days.get(day_number=1)
        day2 = plan.days.get(day_number=2)

        self.client.force_authenticate(user=self.user1)

        # Check day1 detail
        response = self.client.get(f"/api/learning/plans/{plan.id}/days/{day1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["vocabularies"]), 2)
        self.assertEqual(len(response.data["grammars"]), 1)
        self.assertEqual(response.data["progress"]["learned"], 0)

        # Mark 1 vocabulary learned in day1
        v1 = day1.vocabularies.first().vocabulary
        self.client.post(f"/api/learning/vocabularies/{v1.id}/learn/")

        # Verify Day 1 progress (1/3)
        res_day1 = self.client.get(f"/api/learning/plans/{plan.id}/days/{day1.id}/")
        self.assertEqual(res_day1.data["progress"]["learned"], 1)
        self.assertEqual(res_day1.data["progress"]["total"], 3)
        self.assertFalse(res_day1.data["progress"]["completed"])

        # Verify Day 2 progress remains unchanged (0/3) - NO CARRY-OVER
        res_day2 = self.client.get(f"/api/learning/plans/{plan.id}/days/{day2.id}/")
        self.assertEqual(res_day2.data["progress"]["learned"], 0)
        self.assertEqual(res_day2.data["progress"]["total"], 3)

    def test_day_completed_days_and_plan_progress(self):
        plan = StudyPlanService.create_plan(user=self.user1, level=JLPTLevel.N5, total_days=2)
        day1 = plan.days.get(day_number=1)

        self.client.force_authenticate(user=self.user1)

        # Mark all assigned items in Day 1 as learned
        for dv in day1.vocabularies.all():
            self.client.post(f"/api/learning/vocabularies/{dv.vocabulary.id}/learn/")
        for dg in day1.grammars.all():
            self.client.post(f"/api/learning/grammars/{dg.grammar.id}/learn/")

        # Day 1 should now be completed
        res_day1 = self.client.get(f"/api/learning/plans/{plan.id}/days/{day1.id}/progress/")
        self.assertTrue(res_day1.data["completed"])
        self.assertEqual(res_day1.data["percentage"], 100.0)

        # Overall Plan progress check
        res_plan = self.client.get(f"/api/learning/plans/{plan.id}/progress/")
        self.assertEqual(res_plan.data["completed_days"], 1)
        self.assertEqual(res_plan.data["total_days"], 2)

    def test_mark_learned_idempotent(self):
        self.client.force_authenticate(user=self.user1)
        v = self.vocabs[0]

        # First call
        res1 = self.client.post(f"/api/learning/vocabularies/{v.id}/learn/")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        learned_at_1 = res1.data["learned_at"]

        # Second call
        res2 = self.client.post(f"/api/learning/vocabularies/{v.id}/learn/")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        learned_at_2 = res2.data["learned_at"]

        # Timestamp and record count must remain identical
        self.assertEqual(learned_at_1, learned_at_2)
        self.assertEqual(UserVocabulary.objects.filter(user=self.user1, vocabulary=v).count(), 1)

    def test_transaction_rollback_on_failure(self):
        # Test that if an exception occurs during plan creation, transaction rolls back
        with patch.object(DayVocabulary.objects, "bulk_create", side_effect=RuntimeError("Database failure")):
            with self.assertRaises(RuntimeError):
                StudyPlanService.create_plan(user=self.user1, level=JLPTLevel.N5, total_days=5)

        # Ensure no orphan StudyPlan or StudyPlanDay objects were left behind
        self.assertEqual(StudyPlan.objects.count(), 0)
        self.assertEqual(StudyPlanDay.objects.count(), 0)
