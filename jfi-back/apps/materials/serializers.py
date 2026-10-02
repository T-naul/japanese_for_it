from rest_framework import serializers

from apps.content.models import Grammar, Vocabulary
from apps.jobs.models import ProcessingJob
from apps.materials.models import (
    LearningMaterial,
    MaterialLesson,
    MaterialSection,
    UserMaterial,
    UserMaterialLesson,
)


class ProcessingJobSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = ProcessingJob
        fields = [
            "job_id",
            "job_type",
            "status",
            "progress",
            "current_step",
            "error_message",
            "result",
            "created_at",
            "started_at",
            "completed_at",
        ]


class ProcessingStatusSerializer(serializers.Serializer):
    job_id = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField(allow_null=True)
    current_step = serializers.CharField(allow_blank=True)
    error_message = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    started_at = serializers.DateTimeField(allow_null=True, required=False)
    completed_at = serializers.DateTimeField(allow_null=True, required=False)


class MaterialListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningMaterial
        fields = [
            "id",
            "title",
            "description",
            "material_type",
            "level",
            "language",
            "file_size",
            "page_count",
            "status",
            "created_at",
            "updated_at",
        ]


class MaterialDetailSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LearningMaterial
        fields = [
            "id",
            "title",
            "description",
            "material_type",
            "level",
            "language",
            "file_size",
            "page_count",
            "status",
            "metadata",
            "file_url",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        if obj.file:
            try:
                return obj.file.url
            except Exception:
                return None
        return None


class MaterialCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    material_type = serializers.CharField(required=False, default="pdf")
    level = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(required=False, default="ja")
    metadata = serializers.JSONField(required=False, default=dict)
    file = serializers.FileField()


    def validate(self, attrs):
        disallowed = ["status", "page_count", "error_message", "id", "created_at", "updated_at"]
        for field in disallowed:
            if field in self.initial_data:
                raise serializers.ValidationError({field: f"Field '{field}' cannot be set directly."})
        return attrs


class MaterialCreateResponseSerializer(serializers.Serializer):
    material = MaterialDetailSerializer()
    job = ProcessingStatusSerializer()


class MaterialUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=300)
    description = serializers.CharField(required=False, allow_blank=True)
    level = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False)
    metadata = serializers.JSONField(required=False)
    file = serializers.FileField(required=False)

    def validate(self, attrs):
        disallowed = ["status", "page_count", "error_message", "id", "created_at", "updated_at"]
        for field in disallowed:
            if field in self.initial_data:
                raise serializers.ValidationError({field: f"Field '{field}' cannot be modified directly."})
        return attrs


class MaterialLessonListSerializer(serializers.ModelSerializer):
    is_completed = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = MaterialLesson
        fields = [
            "id",
            "title",
            "lesson_number",
            "description",
            "page_start",
            "page_end",
            "is_completed",
        ]


class MaterialLessonDetailSerializer(serializers.ModelSerializer):
    is_completed = serializers.BooleanField(read_only=True, default=False)
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = MaterialLesson
        fields = [
            "id",
            "title",
            "lesson_number",
            "description",
            "page_start",
            "page_end",
            "content",
            "metadata",
            "is_completed",
            "sections_count",
        ]

    def get_sections_count(self, obj):
        return obj.sections.count()


class VocabularySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vocabulary
        fields = ["id", "kanji", "hiragana", "meaning", "level"]


class GrammarSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Grammar
        fields = ["id", "pattern", "meaning", "level"]


class MaterialSectionSerializer(serializers.ModelSerializer):
    vocabulary = VocabularySummarySerializer(read_only=True)
    grammar = GrammarSummarySerializer(read_only=True)

    class Meta:
        model = MaterialSection
        fields = [
            "id",
            "title",
            "section_type",
            "order",
            "page_start",
            "page_end",
            "content",
            "data",
            "vocabulary",
            "grammar",
        ]


class UserMaterialLessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="lesson.id", read_only=True)
    lesson_number = serializers.IntegerField(source="lesson.lesson_number", read_only=True)
    title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = UserMaterialLesson
        fields = [
            "id",
            "lesson_id",
            "lesson_number",
            "title",
            "completed",
            "started_at",
            "completed_at",
        ]


class UserMaterialListSerializer(serializers.ModelSerializer):
    material = MaterialListSerializer(read_only=True)
    progress = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()

    class Meta:
        model = UserMaterial
        fields = [
            "id",
            "material",
            "status",
            "progress",
            "completed_lessons",
            "total_lessons",
            "started_at",
            "completed_at",
        ]

    def get_total_lessons(self, obj):
        return obj.material.lessons.count()

    def get_completed_lessons(self, obj):
        return obj.lessons.filter(completed=True).count()

    def get_progress(self, obj):
        total = self.get_total_lessons(obj)
        if total == 0:
            return 0.0
        completed = self.get_completed_lessons(obj)
        return round((completed / total) * 100.0, 2)


class UserMaterialDetailSerializer(serializers.ModelSerializer):
    material = MaterialDetailSerializer(read_only=True)
    progress = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()
    lessons = UserMaterialLessonSerializer(many=True, read_only=True)

    class Meta:
        model = UserMaterial
        fields = [
            "id",
            "material",
            "status",
            "progress",
            "completed_lessons",
            "total_lessons",
            "lessons",
            "started_at",
            "completed_at",
        ]

    def get_total_lessons(self, obj):
        return obj.material.lessons.count()

    def get_completed_lessons(self, obj):
        return obj.lessons.filter(completed=True).count()

    def get_progress(self, obj):
        total = self.get_total_lessons(obj)
        if total == 0:
            return 0.0
        completed = self.get_completed_lessons(obj)
        return round((completed / total) * 100.0, 2)


class LessonCompletionResponseSerializer(serializers.Serializer):
    lesson_id = serializers.CharField()
    completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    material_progress = serializers.FloatField()
    material_status = serializers.CharField()
