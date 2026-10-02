from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ProcessingJob
from .serializers import JobDetailSerializer


@extend_schema(
    tags=["Jobs"],
    summary="Retrieve Processing Job Detail",
    description="Inspect background processing job status and progress.",
    responses={200: JobDetailSerializer},
)
class JobDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobDetailSerializer
    queryset = ProcessingJob.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "job_id"

    def get_object(self):
        job = super().get_object()
        user = self.request.user
        if not (user.is_staff or job.user == user):
            raise PermissionDenied("You do not have permission to view this job.")
        return job
