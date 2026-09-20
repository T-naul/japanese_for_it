import uuid

from django.conf import settings
from django.db import models


class ReviewSessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"


class ReviewContentType(models.TextChoices):
    VOCABULARY = "vocabulary", "Vocabulary"
    GRAMMAR = "grammar", "Grammar"


class ReviewQuestionType(models.TextChoices):
    MEANING_CHOICE = "meaning_choice", "Meaning Choice"
    TRUE_FALSE = "true_false", "True / False"
    TRANSLATION = "translation", "Translation"


class ReviewSession(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_sessions",
    )

    status = models.CharField(
        max_length=20,
        choices=ReviewSessionStatus.choices,
        default=ReviewSessionStatus.ACTIVE,
    )

    total_questions = models.PositiveIntegerField(default=0)
    answered_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - Review {self.id}"


class ReviewQuestion(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    session = models.ForeignKey(
        ReviewSession,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    content_type = models.CharField(
        max_length=20,
        choices=ReviewContentType.choices,
    )

    vocabulary = models.ForeignKey(
        "content.Vocabulary",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_questions",
    )

    grammar = models.ForeignKey(
        "content.Grammar",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_questions",
    )

    question_type = models.CharField(
        max_length=30,
        choices=ReviewQuestionType.choices,
    )

    prompt = models.TextField()

    # JSON chứa choices cho meaning_choice / true_false.
    # Ví dụ:
    # [
    #   {"id": "A", "text": "ăn"},
    #   {"id": "B", "text": "uống"}
    # ]
    choices = models.JSONField(
        default=list,
        blank=True,
    )

    # Không trả field này ra API trước khi user submit.
    correct_answer = models.JSONField()

    # User answer sau khi submit.
    user_answer = models.JSONField(
        null=True,
        blank=True,
    )

    answered_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_correct = models.BooleanField(
        null=True,
        blank=True,
    )

    order = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["session", "order"],
                name="unique_review_question_order",
            ),
        ]

    def __str__(self):
        return f"{self.session} - Question {self.order}"