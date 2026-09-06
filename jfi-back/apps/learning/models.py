# apps/learning/models.py

import uuid

from django.conf import settings
from django.db import models

from apps.content.models import JLPTLevel


class StudyPlanStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class StudyPlan(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_plans",
    )

    level = models.CharField(
        max_length=2,
        choices=JLPTLevel.choices,
    )

    total_days = models.PositiveIntegerField()

    start_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=StudyPlanStatus.choices,
        default=StudyPlanStatus.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.level} - {self.total_days} days"
    
class StudyPlanDay(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name="days",
    )

    day_number = models.PositiveIntegerField()

    date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["day_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["study_plan", "day_number"],
                name="unique_study_plan_day_number",
            ),
            models.UniqueConstraint(
                fields=["study_plan", "date"],
                name="unique_study_plan_day_date",
            ),
        ]

    def __str__(self):
        return f"{self.study_plan} - Day {self.day_number}"


class DayVocabulary(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    study_plan_day = models.ForeignKey(
        StudyPlanDay,
        on_delete=models.CASCADE,
        related_name="vocabularies",
    )

    vocabulary = models.ForeignKey(
        "content.Vocabulary",
        on_delete=models.CASCADE,
        related_name="study_plan_days",
    )

    # is_carry_over = models.BooleanField(
    #     default=False,
    # )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "study_plan_day",
                    "vocabulary",
                ],
                name="unique_day_vocabulary",
            )
        ]

    def __str__(self):
        return f"{self.study_plan_day} - {self.vocabulary}"

class DayGrammar(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    study_plan_day = models.ForeignKey(
        StudyPlanDay,
        on_delete=models.CASCADE,
        related_name="grammars",
    )

    grammar = models.ForeignKey(
        "content.Grammar",
        on_delete=models.CASCADE,
        related_name="study_plan_days",
    )

    # is_carry_over = models.BooleanField(
    #     default=False,
    # )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "study_plan_day",
                    "grammar",
                ],
                name="unique_day_grammar",
            )
        ]

    def __str__(self):
        return f"{self.study_plan_day} - {self.grammar}"
