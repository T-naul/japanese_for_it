from rest_framework.routers import DefaultRouter

from .views import (
    GrammarViewSet,
    SourceViewSet,
    VocabularyViewSet,
)

router = DefaultRouter()

router.register(
    "vocabularies",
    VocabularyViewSet,
    basename="vocabulary",
)

router.register(
    "grammars",
    GrammarViewSet,
    basename="grammar",
)

router.register(
    "sources",
    SourceViewSet,
    basename="source",
)

urlpatterns = router.urls