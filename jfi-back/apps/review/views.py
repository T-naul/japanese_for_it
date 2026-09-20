# apps/review/views.py

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReviewSession
from .serializers import (
    ReviewAvailableSerializer,
    ReviewProgressSerializer,
    ReviewSessionCreateSerializer,
    ReviewSessionSerializer,
    SubmitAnswerSerializer,
)
from .services import ReviewService


class ReviewAvailableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary = ReviewService.get_available_content_summary(request.user)
        return Response(summary, status=status.HTTP_200_OK)


class ReviewSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        return ReviewSession.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewSessionCreateSerializer
        return ReviewSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        limit = serializer.validated_data.get("limit", 10)

        try:
            session = ReviewService.create_session(user=request.user, limit=limit)
            out_serializer = ReviewSessionSerializer(session)
            return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        session = self.get_object()
        progress_data = ReviewService.get_session_progress(request.user, session.id)
        return Response(progress_data, status=status.HTTP_200_OK)


class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, question_id):
        session = get_object_or_404(ReviewSession, id=session_id, user=request.user)
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = ReviewService.submit_answer(
                user=request.user,
                session_id=session.id,
                question_id=question_id,
                user_answer_payload=serializer.validated_data,
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
