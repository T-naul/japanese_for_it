import logging
from typing import Any, Dict, Tuple
from django.db import transaction

from apps.jobs.models import JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.shadowing.models import ShadowingVideo, VideoStatus
from apps.shadowing.processing.validator import VideoValidator
from apps.shadowing.tasks import process_shadowing_video

logger = logging.getLogger(__name__)


class ShadowingVideoService:
    """
    Coordinates creation, validation, and asynchronous processing dispatch
    for ShadowingVideo resources.
    """

    @staticmethod
    def create_video(user, data: Dict[str, Any], file_obj) -> Tuple[ShadowingVideo, ProcessingJob]:
        """
        Validates uploaded video file and metadata, creates ShadowingVideo record
        and associated ProcessingJob, and schedules Celery background task post-commit.
        Returns (video, job).
        """
        # Validate video file format, size, etc.
        VideoValidator.validate_uploaded_file(file_obj)

        title = data.get("title", "").strip()
        if not title:
            from apps.shadowing.processing.exceptions import VideoValidationError
            raise VideoValidationError("Title is required.")

        description = data.get("description", "")
        language = data.get("language", "ja")
        level = data.get("level", "")
        metadata = dict(data.get("metadata", {}))

        with transaction.atomic():
            video = ShadowingVideo.objects.create(
                title=title,
                description=description,
                language=language,
                level=level,
                video_file=file_obj,
                file_size=file_obj.size if hasattr(file_obj, "size") else None,
                status=VideoStatus.UPLOAD,
                metadata=metadata,
            )

            # Create ProcessingJob
            job = ProcessingJobService.create_job(
                user=user,
                job_type=JobType.VIDEO_PROCESSING,
                result={"video_id": str(video.id)},
            )

            video.metadata["job_id"] = str(job.id)
            video.save(update_fields=["metadata", "updated_at"])

            # Dispatch Celery worker asynchronously after DB transaction commits
            transaction.on_commit(
                lambda: process_shadowing_video.delay(str(video.id), str(job.id))
            )

        logger.info("Created ShadowingVideo id=%s with ProcessingJob id=%s", video.id, job.id)
        return video, job
