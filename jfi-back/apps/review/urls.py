# apps/review/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ReviewAvailableView,
    ReviewSessionViewSet,
    SubmitAnswerView,
)

router = DefaultRouter()
router.register("sessions", ReviewSessionViewSet, basename="review-session")

urlpatterns = [
    path("available/", ReviewAvailableView.as_view(), name="review-available"),
    path(
        "sessions/<uuid:session_id>/questions/<uuid:question_id>/answer/",
        SubmitAnswerView.as_view(),
        name="review-submit-answer",
    ),
    path("", include(router.urls)),
]
