# apps/learning/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MarkGrammarLearnedView,
    MarkVocabularyLearnedView,
    StudyPlanDayDetailView,
    StudyPlanDayProgressView,
    StudyPlanDaysListView,
    StudyPlanViewSet,
)

router = DefaultRouter()
router.register("plans", StudyPlanViewSet, basename="study-plan")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "plans/<uuid:plan_id>/days/",
        StudyPlanDaysListView.as_view(),
        name="study-plan-days-list",
    ),
    path(
        "plans/<uuid:plan_id>/days/<uuid:day_id>/",
        StudyPlanDayDetailView.as_view(),
        name="study-plan-day-detail",
    ),
    path(
        "plans/<uuid:plan_id>/days/<uuid:day_id>/progress/",
        StudyPlanDayProgressView.as_view(),
        name="study-plan-day-progress",
    ),
    path(
        "vocabularies/<uuid:vocabulary_id>/learn/",
        MarkVocabularyLearnedView.as_view(),
        name="mark-vocabulary-learned",
    ),
    path(
        "grammars/<uuid:grammar_id>/learn/",
        MarkGrammarLearnedView.as_view(),
        name="mark-grammar-learned",
    ),
]
