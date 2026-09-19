# pyrefly: ignore [missing-import]
from rest_framework import viewsets

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


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    pagination_class = StandardResultsSetPagination

    # permission_classes = [
    #     IsAdminUser,
    # ]