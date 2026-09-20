# apps/review/serializers.py

from rest_framework import serializers
from .models import ReviewQuestion, ReviewSession


class ReviewSessionCreateSerializer(serializers.Serializer):
    limit = serializers.IntegerField(default=10, min_value=1, max_value=50)


class ReviewQuestionSerializer(serializers.ModelSerializer):
    content_id = serializers.SerializerMethodField()
    answered = serializers.SerializerMethodField()

    class Meta:
        model = ReviewQuestion
        fields = [
            "id",
            "question_type",
            "content_type",
            "content_id",
            "prompt",
            "choices",
            "order",
            "answered",
        ]

    def get_content_id(self, obj):
        if obj.vocabulary_id:
            return str(obj.vocabulary_id)
        if obj.grammar_id:
            return str(obj.grammar_id)
        return None

    def get_answered(self, obj):
        return obj.answered_at is not None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Chỉ hiển thị kết quả đúng/sai và đáp án SAU khi câu hỏi đã được trả lời
        if instance.answered_at is not None:
            ret["user_answer"] = instance.user_answer
            ret["is_correct"] = instance.is_correct
            if isinstance(instance.correct_answer, dict):
                ret["correct_answer"] = (
                    instance.correct_answer.get("choice_id")
                    or instance.correct_answer.get("answer_text")
                )
            else:
                ret["correct_answer"] = instance.correct_answer
        return ret


class ReviewSessionSerializer(serializers.ModelSerializer):
    questions = ReviewQuestionSerializer(many=True, read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = ReviewSession
        fields = [
            "id",
            "status",
            "total_questions",
            "answered_questions",
            "correct_answers",
            "percentage",
            "created_at",
            "completed_at",
            "questions",
        ]

    def get_percentage(self, obj):
        if obj.total_questions > 0:
            return round(obj.correct_answers / obj.total_questions * 100, 2)
        return 0.0


class SubmitAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(required=True)


class ReviewProgressSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    status = serializers.CharField()
    total_questions = serializers.IntegerField()
    answered_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    percentage = serializers.FloatField()
    completed = serializers.BooleanField()


class ReviewAvailableSerializer(serializers.Serializer):
    available = serializers.BooleanField()
    reason = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    vocabulary_count = serializers.IntegerField()
    grammar_count = serializers.IntegerField()
    total = serializers.IntegerField()
