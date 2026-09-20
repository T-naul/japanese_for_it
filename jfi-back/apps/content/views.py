# pyrefly: ignore [missing-import]
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Grammar, Source, Vocabulary
from .pagination import StandardResultsSetPagination
from .serializers import (
    FileImportSerializer,
    GrammarSerializer,
    SourceSerializer,
    VocabularyDetailSerializer,
    VocabularyListSerializer,
)
from .services import GrammarService, VocabularyService


class VocabularyViewSet(viewsets.ModelViewSet):
    queryset = Vocabulary.objects.all().prefetch_related(
        "forms",
        "synonyms",
        "sources",
    )
    pagination_class = StandardResultsSetPagination

    # permission_classes = [
    #     IsAdminUser,
    # ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "level",
        "word_type",
        "status",
    ]
    search_fields = [
        "kanji",
        "hiragana",
        "han_viet",
        "meaning",
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return VocabularyListSerializer

        return VocabularyDetailSerializer

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        url_path="import_file",
    )
    def import_file(self, request):
        serializer = FileImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data["file"]

        try:
            result = VocabularyService.import_from_file(file_obj)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GrammarViewSet(viewsets.ModelViewSet):
    queryset = Grammar.objects.all().prefetch_related(
        "sources",
    )
    serializer_class = GrammarSerializer
    pagination_class = StandardResultsSetPagination

    # permission_classes = [
    #     IsAdminUser,
    # ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "level",
        "status",
    ]
    search_fields = [
        "pattern",
        "meaning",
    ]

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        url_path="import_file",
    )
    def import_file(self, request):
        serializer = FileImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data["file"]

        try:
            result = GrammarService.import_from_file(file_obj)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    pagination_class = StandardResultsSetPagination

    # permission_classes = [
    #     IsAdminUser,
    # ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]
    search_fields = [
        "name",
    ]
    filterset_fields = [
        "name",
    ]