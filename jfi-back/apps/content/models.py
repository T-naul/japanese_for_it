from django.db import models

import uuid


class JLPTLevel(models.TextChoices):
    N5 = "N5", "N5"
    N4 = "N4", "N4"
    N3 = "N3", "N3"
    N2 = "N2", "N2"
    N1 = "N1", "N1"


class ContentStatus(models.TextChoices):
    UPLOAD = "upload", "Upload"
    REVIEW = "review", "Review"
    ACCEPTED = "accepted", "Accepted"


class WordType(models.TextChoices):
    NOUN = "noun", "Danh từ"
    VERB = "verb", "Động từ"
    ADJECTIVE = "adjective", "Tính từ"


class VerbFormType(models.TextChoices):
    DICTIONARY = "dictionary", "Dictionary"
    MASU = "masu", "ます形"
    NAI = "nai", "ない形"
    TA = "ta", "た形"
    TE = "te", "て形"
    NAKATTA = "nakatta", "なかった形"
    POTENTIAL = "potential", "可能形"
    PASSIVE = "passive", "受身形"
    CAUSATIVE = "causative", "使役形"
    IMPERATIVE = "imperative", "命令形"


class Source(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=200,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.name


class Vocabulary(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    kanji = models.CharField(max_length=100)
    hiragana = models.CharField(max_length=100)
    han_viet = models.CharField(
        max_length=100,
        blank=True,
    )

    meaning = models.TextField()

    word_type = models.CharField(
        max_length=20,
        choices=WordType.choices,
    )

    level = models.CharField(
        max_length=2,
        choices=JLPTLevel.choices,
    )

    example = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    version = models.PositiveIntegerField(
        default=1,
    )

    status = models.CharField(
        max_length=20,
        choices=ContentStatus.choices,
        default=ContentStatus.UPLOAD,
    )

    synonyms = models.ManyToManyField(
        "self",
        symmetrical=True,
        blank=True,
    )

    sources = models.ManyToManyField(
        Source,
        blank=True,
        related_name="vocabularies",
    )

    def __str__(self):
        return f"{self.kanji} ({self.hiragana})"


class VocabularyForm(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    vocabulary = models.ForeignKey(
        Vocabulary,
        on_delete=models.CASCADE,
        related_name="forms",
    )

    form_type = models.CharField(
        max_length=30,
        choices=VerbFormType.choices,
    )

    value = models.CharField(
        max_length=100,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vocabulary", "form_type"],
                name="unique_vocabulary_form_type",
            )
        ]

    def __str__(self):
        return f"{self.vocabulary.kanji} - {self.get_form_type_display()}"


class Grammar(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    pattern = models.CharField(
        max_length=200,
    )

    meaning = models.TextField()

    level = models.CharField(
        max_length=2,
        choices=JLPTLevel.choices,
    )

    example = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    version = models.PositiveIntegerField(
        default=1,
    )

    status = models.CharField(
        max_length=20,
        choices=ContentStatus.choices,
        default=ContentStatus.UPLOAD,
    )

    sources = models.ManyToManyField(
        Source,
        blank=True,
        related_name="grammars",
    )

    def __str__(self):
        return self.pattern
