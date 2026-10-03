from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    ShadowingSegment,
    ShadowingVideo,
    UserShadowingSegment,
    UserShadowingStatus,
    UserShadowingVideo,
)


class ShadowingProcessingStatusSerializer(serializers.Serializer):
    job_id = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField(allow_null=True)
    current_step = serializers.CharField(allow_blank=True)
    error_message = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    started_at = serializers.DateTimeField(allow_null=True, required=False)
    completed_at = serializers.DateTimeField(allow_null=True, required=False)


class ShadowingSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShadowingSegment
        fields = [
            "id",
            "sequence",
            "start_time",
            "end_time",
            "text",
            "reading",
            "speaker",
            "metadata",
        ]
        read_only_fields = fields


class ShadowingVideoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShadowingVideo
        fields = [
            "id",
            "title",
            "description",
            "level",
            "language",
            "duration_seconds",
            "file_size",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ShadowingVideoDetailSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = ShadowingVideo
        fields = [
            "id",
            "title",
            "description",
            "level",
            "language",
            "duration_seconds",
            "file_size",
            "status",
            "metadata",
            "video_url",
            "audio_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_video_url(self, obj) -> str | None:
        if obj.video_file:
            try:
                return obj.video_file.url
            except Exception:
                return None
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_audio_url(self, obj) -> str | None:
        if obj.audio_file:
            try:
                return obj.audio_file.url
            except Exception:
                return None
        return None


class ShadowingVideoCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    level = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(required=False, default="ja")
    metadata = serializers.JSONField(required=False, default=dict)
    video_file = serializers.FileField()

    def validate_video_file(self, value):
        from apps.shadowing.processing.validator import VideoValidator
        from apps.shadowing.processing.exceptions import VideoValidationError
        try:
            VideoValidator.validate_uploaded_file(value)
        except VideoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        disallowed = [
            "id",
            "status",
            "duration_seconds",
            "file_size",
            "audio_file",
            "error_message",
            "created_at",
            "updated_at",
            "job_id",
        ]
        for field in disallowed:
            if field in self.initial_data:
                raise serializers.ValidationError({field: f"Field '{field}' cannot be set directly."})
        return attrs


class ShadowingVideoCreateResponseSerializer(serializers.Serializer):
    video = ShadowingVideoDetailSerializer()
    job = ShadowingProcessingStatusSerializer(allow_null=True)


class ShadowingVideoUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=300)
    description = serializers.CharField(required=False, allow_blank=True)
    level = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False)
    metadata = serializers.JSONField(required=False)
    video_file = serializers.FileField(required=False)

    def validate_video_file(self, value):
        if value:
            from apps.shadowing.processing.validator import VideoValidator
            from apps.shadowing.processing.exceptions import VideoValidationError
            try:
                VideoValidator.validate_uploaded_file(value)
            except VideoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value

    def validate(self, attrs):
        disallowed = [
            "id",
            "status",
            "duration_seconds",
            "file_size",
            "audio_file",
            "error_message",
            "created_at",
            "updated_at",
            "job_id",
        ]
        for field in disallowed:
            if field in self.initial_data:
                raise serializers.ValidationError({field: f"Field '{field}' cannot be modified directly."})
        return attrs


class UserShadowingSegmentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="segment.id", read_only=True)
    sequence = serializers.IntegerField(source="segment.sequence", read_only=True)
    text = serializers.CharField(source="segment.text", read_only=True)
    reading = serializers.CharField(source="segment.reading", read_only=True)
    speaker = serializers.CharField(source="segment.speaker", read_only=True)
    start_time = serializers.FloatField(source="segment.start_time", read_only=True)
    end_time = serializers.FloatField(source="segment.end_time", read_only=True)
    start_seconds = serializers.FloatField(source="segment.start_time", read_only=True)
    end_seconds = serializers.FloatField(source="segment.end_time", read_only=True)
    is_completed = serializers.BooleanField(source="completed", read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserShadowingSegment
        fields = [
            "id",
            "sequence",
            "text",
            "reading",
            "speaker",
            "start_time",
            "end_time",
            "start_seconds",
            "end_seconds",
            "is_completed",
            "completed_at",
        ]


class UserShadowingListSerializer(serializers.ModelSerializer):
    video = ShadowingVideoListSerializer(read_only=True)
    video_id = serializers.UUIDField(source="video.id", read_only=True)
    title = serializers.CharField(source="video.title", read_only=True)
    level = serializers.CharField(source="video.level", read_only=True)
    language = serializers.CharField(source="video.language", read_only=True)
    completed_segments = serializers.SerializerMethodField()
    total_segments = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserShadowingVideo
        fields = [
            "id",
            "video_id",
            "title",
            "level",
            "language",
            "video",
            "status",
            "completed_segments",
            "total_segments",
            "percentage",
            "started_at",
            "completed_at",
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_total_segments(self, obj) -> int:
        return obj.video.segments.count()

    @extend_schema_field(serializers.IntegerField())
    def get_completed_segments(self, obj) -> int:
        return obj.segment_progress.filter(completed=True).count()

    @extend_schema_field(serializers.FloatField())
    def get_percentage(self, obj) -> float:
        total = self.get_total_segments(obj)
        if total == 0:
            return 0.0
        completed = self.get_completed_segments(obj)
        return round((completed / total) * 100.0, 2)


class UserShadowingProgressSerializer(serializers.Serializer):
    completed_segments = serializers.IntegerField()
    total_segments = serializers.IntegerField()
    percentage = serializers.FloatField()
    completed = serializers.BooleanField()


class UserShadowingDetailSerializer(serializers.ModelSerializer):
    video = ShadowingVideoDetailSerializer(read_only=True)
    progress = serializers.SerializerMethodField()
    segments = UserShadowingSegmentSerializer(source="segment_progress", many=True, read_only=True)

    class Meta:
        model = UserShadowingVideo
        fields = [
            "id",
            "video",
            "status",
            "progress",
            "segments",
            "started_at",
            "completed_at",
        ]

    @extend_schema_field(UserShadowingProgressSerializer)
    def get_progress(self, obj) -> dict:
        total = obj.video.segments.count()
        completed = obj.segment_progress.filter(completed=True).count()
        pct = round((completed / total) * 100.0, 2) if total > 0 else 0.0
        return {
            "completed_segments": completed,
            "total_segments": total,
            "percentage": pct,
            "completed": (obj.status == UserShadowingStatus.COMPLETED),
        }


class SegmentCompletionResponseSerializer(serializers.Serializer):
    segment_id = serializers.CharField()
    completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    completed_segments = serializers.IntegerField()
    total_segments = serializers.IntegerField()
    percentage = serializers.FloatField()
    video_status = serializers.CharField()


class EnrollmentResponseSerializer(serializers.Serializer):
    enrolled = serializers.BooleanField()
    video_id = serializers.CharField()
    status = serializers.CharField()
