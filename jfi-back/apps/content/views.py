# pyrefly: ignore [missing-import]
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Grammar, Source, Vocabulary
from .pagination import StandardResultsSetPagination
from .serializers import (
    GrammarSerializer,
    SourceSerializer,
    VocabularyDetailSerializer,
    VocabularyListSerializer,
)


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