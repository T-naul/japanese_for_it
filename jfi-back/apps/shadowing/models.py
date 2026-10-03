import uuid
from django.db import models


class VideoStatus(models.TextChoices):
    UPLOAD = "upload", "Upload"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class ShadowingVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    language = models.CharField(max_length=20, default="ja")
    level = models.CharField(max_length=20, blank=True, default="")

    video_file = models.FileField(upload_to="shadowing/videos/")
    audio_file = models.FileField(upload_to="shadowing/audio/", blank=True, null=True)

    duration_seconds = models.FloatField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=VideoStatus.choices,
        default=VideoStatus.UPLOAD,
    )
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"


class ShadowingSegment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(
        ShadowingVideo,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    sequence = models.PositiveIntegerField()
    start_time = models.FloatField()
    end_time = models.FloatField()
    text = models.TextField()
    reading = models.TextField(blank=True, default="")
    speaker = models.CharField(max_length=100, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["video", "sequence"],
                name="unique_shadowing_segment_video_sequence",
            ),
            models.CheckConstraint(
                check=models.Q(end_time__gte=models.F("start_time")),
                name="shadowing_segment_end_gte_start",
            ),
        ]

    def __str__(self):
        return f"{self.video_id} - Seq {self.sequence}: {self.start_time:.2f}s - {self.end_time:.2f}s"
