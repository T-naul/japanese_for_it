import uuid

from django.conf import settings
from django.db import models


class MaterialType(models.TextChoices):
    PDF = "pdf", "PDF"
    DOCUMENT = "document", "Document"
    BOOK = "book", "Book"
    OTHER = "other", "Other"


class MaterialStatus(models.TextChoices):
    UPLOAD = "upload", "Upload"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class MaterialSectionType(models.TextChoices):
    TEXT = "text", "Text"
    VOCABULARY = "vocabulary", "Vocabulary"
    GRAMMAR = "grammar", "Grammar"
    DIALOGUE = "dialogue", "Dialogue"
    READING = "reading", "Reading"
    EXERCISE = "exercise", "Exercise"
    EXPLANATION = "explanation", "Explanation"
    NOTE = "note", "Note"
    TABLE = "table", "Table"
    IMAGE = "image", "Image"
    CUSTOM = "custom", "Custom"


class UserMaterialStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"


class LearningMaterial(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    title = models.CharField(max_length=300)

    description = models.TextField(blank=True)

    material_type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        default=MaterialType.PDF,
    )

    level = models.CharField(
        max_length=2,
        choices=[
            ("N5", "N5"),
            ("N4", "N4"),
            ("N3", "N3"),
            ("N2", "N2"),
            ("N1", "N1"),
        ],
        blank=True,
    )

    language = models.CharField(
        max_length=20,
        default="ja",
    )

    file = models.FileField(
        upload_to="materials/",
        blank=True,
        null=True,
    )

    file_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    page_count = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=MaterialStatus.choices,
        default=MaterialStatus.UPLOAD,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
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
        return self.title


class MaterialLesson(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name="lessons",
    )

    title = models.CharField(
        max_length=300,
    )

    lesson_number = models.PositiveIntegerField()

    description = models.TextField(
        blank=True,
    )

    page_start = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    page_end = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    content = models.TextField(
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["lesson_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["material", "lesson_number"],
                name="unique_material_lesson_number",
            ),
        ]

    def __str__(self):
        return f"{self.material.title} - Lesson {self.lesson_number}"


class MaterialSection(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    lesson = models.ForeignKey(
        MaterialLesson,
        on_delete=models.CASCADE,
        related_name="sections",
    )

    title = models.CharField(
        max_length=300,
        blank=True,
    )

    section_type = models.CharField(
        max_length=30,
        choices=MaterialSectionType.choices,
        default=MaterialSectionType.TEXT,
    )

    order = models.PositiveIntegerField()

    page_start = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    page_end = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    content = models.TextField(
        blank=True,
    )

    data = models.JSONField(
        default=dict,
        blank=True,
    )

    vocabulary = models.ForeignKey(
        "content.Vocabulary",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="material_sections",
    )

    grammar = models.ForeignKey(
        "content.Grammar",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="material_sections",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["order"]

        constraints = [
            models.UniqueConstraint(
                fields=["lesson", "order"],
                name="unique_material_section_order",
            ),
        ]

    def __str__(self):
        return f"{self.lesson} - {self.order}"


class UserMaterial(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="materials",
    )

    material = models.ForeignKey(
        LearningMaterial,
        on_delete=models.CASCADE,
        related_name="user_materials",
    )

    status = models.CharField(
        max_length=20,
        choices=UserMaterialStatus.choices,
        default=UserMaterialStatus.ACTIVE,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
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
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "material"],
                name="unique_user_material",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.material}"


class UserMaterialLesson(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user_material = models.ForeignKey(
        UserMaterial,
        on_delete=models.CASCADE,
        related_name="lessons",
    )

    lesson = models.ForeignKey(
        MaterialLesson,
        on_delete=models.CASCADE,
        related_name="user_progress",
    )

    completed = models.BooleanField(
        default=False,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
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
        ordering = ["lesson__lesson_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["user_material", "lesson"],
                name="unique_user_material_lesson",
            ),
        ]

    def __str__(self):
        return f"{self.user_material} - {self.lesson}"