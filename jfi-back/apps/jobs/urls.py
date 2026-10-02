from django.urls import path
from .views import JobDetailView

urlpatterns = [
    path("<uuid:job_id>/", JobDetailView.as_view(), name="job-detail"),
]
