from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

import uuid
from django.conf import settings

class User(AbstractUser):
    pass

class UserVocabulary(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocabulary_progress",
    )

    vocabulary = models.ForeignKey(
        "content.Vocabulary",
        on_delete=models.CASCADE,
        related_name="user_progress",
    )

    learned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "vocabulary"],
                name="unique_user_vocabulary",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.vocabulary}"


class UserGrammar(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grammar_progress",
    )

    grammar = models.ForeignKey(
        "content.Grammar",
        on_delete=models.CASCADE,
        related_name="user_progress",
    )

    learned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "grammar"],
                name="unique_user_grammar",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.grammar}"