# apps/learning/views.py

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import Grammar, Vocabulary
from apps.content.serializers import GrammarSerializer, VocabularyDetailSerializer

from .models import StudyPlan, StudyPlanDay
from .serializers import (
    StudyPlanCreateSerializer,
    StudyPlanDaySerializer,
    StudyPlanSerializer,
    UserGrammarProgressSerializer,
    UserVocabularyProgressSerializer,
)
from .services import LearningService, ProgressService, StudyPlanService


class StudyPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudyPlan.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return StudyPlanCreateSerializer
        return StudyPlanSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        level = serializer.validated_data["level"]
        total_days = serializer.validated_data["total_days"]
        start_date = serializer.validated_data.get("start_date")

        try:
            plan = StudyPlanService.create_plan(
                user=request.user,
                level=level,
                total_days=total_days,
                start_date=start_date,
            )
            output_serializer = StudyPlanSerializer(plan)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="progress")
    def plan_progress(self, request, pk=None):
        plan = self.get_object()
        try:
            progress_data = ProgressService.get_plan_progress(request.user, plan)
            return Response(progress_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudyPlanDaysListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id):
        plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
        days = plan.days.all()
        serializer = StudyPlanDaySerializer(days, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudyPlanDayDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id, day_id):
        plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
        day = get_object_or_404(StudyPlanDay, id=day_id, study_plan=plan)

        content = LearningService.get_day_content(request.user, day)
        progress = ProgressService.get_day_progress(request.user, day)

        vocabularies_data = VocabularyDetailSerializer(content["vocabularies"], many=True).data
        grammars_data = GrammarSerializer(content["grammars"], many=True).data

        return Response(
            {
                "id": day.id,
                "day_number": day.day_number,
                "date": day.date,
                "vocabularies": vocabularies_data,
                "grammars": grammars_data,
                "progress": progress,
            },
            status=status.HTTP_200_OK,
        )


class StudyPlanDayProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, plan_id, day_id):
        plan = get_object_or_404(StudyPlan, id=plan_id, user=request.user)
        day = get_object_or_404(StudyPlanDay, id=day_id, study_plan=plan)
        progress = ProgressService.get_day_progress(request.user, day)
        return Response(progress, status=status.HTTP_200_OK)


class MarkVocabularyLearnedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vocabulary_id):
        vocabulary = get_object_or_404(Vocabulary, id=vocabulary_id)
        user_vocab = LearningService.mark_vocabulary_learned(request.user, vocabulary)
        serializer = UserVocabularyProgressSerializer(user_vocab)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkGrammarLearnedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, grammar_id):
        grammar = get_object_or_404(Grammar, id=grammar_id)
        user_grammar = LearningService.mark_grammar_learned(request.user, grammar)
        serializer = UserGrammarProgressSerializer(user_grammar)
        return Response(serializer.data, status=status.HTTP_200_OK)
