# apps/learning/serializers.py

from rest_framework import serializers

from apps.content.models import Grammar, Vocabulary
from apps.content.serializers import GrammarSerializer, VocabularyDetailSerializer
from apps.users.models import UserGrammar, UserVocabulary

from .models import DayGrammar, DayVocabulary, StudyPlan, StudyPlanDay, StudyPlanStatus


class StudyPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudyPlan
        fields = [
            "id",
            "level",
            "total_days",
            "start_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_total_days(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số ngày học phải lớn hơn 0.")
        return value


class StudyPlanCreateSerializer(serializers.Serializer):
    level = serializers.CharField(max_length=2, required=True)
    total_days = serializers.IntegerField(required=True)
    start_date = serializers.DateField(required=False, allow_null=True)

    def validate_total_days(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số ngày học phải lớn hơn 0.")
        return value


class StudyPlanDaySerializer(serializers.ModelSerializer):

    class Meta:
        model = StudyPlanDay
        fields = [
            "id",
            "day_number",
            "date",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "day_number",
            "date",
            "created_at",
        ]


class UserVocabularyProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserVocabulary
        fields = [
            "id",
            "user",
            "vocabulary",
            "learned_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]


class UserGrammarProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserGrammar
        fields = [
            "id",
            "user",
            "grammar",
            "learned_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]
