from rest_framework import serializers
from .models import ProcessingJob


class JobDetailSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = ProcessingJob
        fields = [
            "job_id",
            "job_type",
            "status",
            "progress",
            "current_step",
            "error_message",
            "result",
            "created_at",
            "started_at",
            "completed_at",
        ]
