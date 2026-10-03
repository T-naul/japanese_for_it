import logging
from typing import Any, Dict, Optional, Tuple

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.shadowing.models import (
    ShadowingSegment,
    ShadowingVideo,
    UserShadowingSegment,
    UserShadowingStatus,
    UserShadowingVideo,
    VideoStatus,
)
from apps.shadowing.processing.exceptions import VideoValidationError
from apps.shadowing.processing.validator import VideoValidator
from apps.shadowing.tasks import process_shadowing_video

logger = logging.getLogger(__name__)


class ConflictError(APIException):
    status_code = 409
    default_detail = "Conflict with current resource state."
    default_code = "conflict"


class ShadowingVideoService:
    """
    Coordinates creation, validation, update, deletion, and querying
    for ShadowingVideo resources.
    """

    @staticmethod
    def get_videos_queryset(user):
        """
        Admins can view all videos in all states.
        Normal users can only view READY videos.
        """
        qs = ShadowingVideo.objects.all()
        if not (user and user.is_staff):
            qs = qs.filter(status=VideoStatus.READY)
        return qs

    @staticmethod
    def create_video(user, data: Dict[str, Any], file_obj) -> Tuple[ShadowingVideo, ProcessingJob]:
        """
        Validates uploaded video file and metadata, creates ShadowingVideo record
        and associated ProcessingJob, and schedules Celery background task post-commit.
        Returns (video, job).
        """
        VideoValidator.validate_uploaded_file(file_obj)

        title = data.get("title", "").strip()
        if not title:
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

            job = ProcessingJobService.create_job(
                user=user,
                job_type=JobType.VIDEO_PROCESSING,
                result={"video_id": str(video.id)},
            )

            video.metadata["job_id"] = str(job.id)
            video.save(update_fields=["metadata", "updated_at"])

            transaction.on_commit(
                lambda: process_shadowing_video.delay(str(video.id), str(job.id))
            )

        logger.info("Created ShadowingVideo id=%s with ProcessingJob id=%s", video.id, job.id)
        return video, job

    @staticmethod
    def update_video(
        video: ShadowingVideo,
        user,
        data: Dict[str, Any],
        file_obj=None,
    ) -> Tuple[ShadowingVideo, Optional[ProcessingJob]]:
        disallowed = [
            "id",
            "status",
            "duration_seconds",
            "file_size",
            "audio_file",
            "error_message",
            "created_at",
            "updated_at",
            "job_id",
        ]
        for field in disallowed:
            if field in data:
                raise ValidationError({field: f"Field '{field}' cannot be modified directly."})

        if "title" in data:
            title = data["title"].strip()
            if not title:
                raise ValidationError({"title": "Title cannot be empty."})
            video.title = title

        if "description" in data:
            video.description = data["description"]

        if "level" in data:
            video.level = data["level"]

        if "language" in data:
            video.language = data["language"]

        if "metadata" in data and isinstance(data["metadata"], dict):
            job_id = video.metadata.get("job_id")
            video.metadata = dict(data["metadata"])
            if job_id:
                video.metadata["job_id"] = job_id

        new_job = None
        if file_obj:
            if video.status == VideoStatus.PROCESSING:
                raise ConflictError("Cannot replace file while video is currently processing.")

            VideoValidator.validate_uploaded_file(file_obj)

            with transaction.atomic():
                # Clean up existing generated segments and progress
                video.segments.all().delete()
                UserShadowingSegment.objects.filter(segment__video=video).delete()

                # Clean old files from storage
                if video.audio_file:
                    try:
                        video.audio_file.delete(save=False)
                    except Exception:
                        pass
                if video.video_file:
                    try:
                        video.video_file.delete(save=False)
                    except Exception:
                        pass

                video.video_file = file_obj
                video.audio_file = None
                video.file_size = file_obj.size if hasattr(file_obj, "size") else None
                video.duration_seconds = None
                video.status = VideoStatus.UPLOAD
                video.error_message = ""

                new_job = ProcessingJobService.create_job(
                    user=user,
                    job_type=JobType.VIDEO_PROCESSING,
                    result={"video_id": str(video.id)},
                )
                video.metadata["job_id"] = str(new_job.id)
                video.save()

                transaction.on_commit(
                    lambda: process_shadowing_video.delay(str(video.id), str(new_job.id))
                )
        else:
            video.save()

        return video, new_job

    @staticmethod
    def delete_video(video: ShadowingVideo) -> None:
        if video.status == VideoStatus.PROCESSING:
            raise ConflictError("Cannot delete video while it is currently processing.")

        with transaction.atomic():
            if video.audio_file:
                try:
                    video.audio_file.delete(save=False)
                except Exception:
                    pass
            if video.video_file:
                try:
                    video.video_file.delete(save=False)
                except Exception:
                    pass
            video.delete()


class ShadowingProcessingService:
    @staticmethod
    def get_video_processing_status(video: ShadowingVideo) -> Optional[Dict[str, Any]]:
        """
        Returns active queued/processing job first, otherwise latest job for the video.
        Never exposes raw stack traces.
        """
        jobs = ProcessingJob.objects.filter(
            result__video_id=str(video.id)
        ).order_by("-created_at")

        job = None
        for j in jobs:
            if j.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                job = j
                break

        if not job:
            job = jobs.first()

        if not job and video.metadata.get("job_id"):
            try:
                job = ProcessingJob.objects.get(id=video.metadata["job_id"])
            except ProcessingJob.DoesNotExist:
                job = None

        if not job:
            return None

        # Clean safe error message without traceback
        err_msg = job.error_message or None
        if err_msg and ("Traceback" in err_msg or "File \"" in err_msg):
            err_msg = err_msg.splitlines()[-1] if err_msg.splitlines() else "Processing failed."

        return {
            "job_id": str(job.id),
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "error_message": err_msg,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }


class ShadowingSegmentService:
    @staticmethod
    def get_segments_for_video(video: ShadowingVideo, user=None):
        return video.segments.all().order_by("sequence")


class ShadowingEnrollmentService:
    @staticmethod
    def enroll_user(user, video: ShadowingVideo) -> Tuple[UserShadowingVideo, bool]:
        if video.status != VideoStatus.READY:
            raise ValidationError("Video is not ready for enrollment.")

        with transaction.atomic():
            user_video, created = UserShadowingVideo.objects.get_or_create(
                user=user,
                video=video,
                defaults={
                    "status": UserShadowingStatus.ACTIVE,
                    "started_at": timezone.now(),
                },
            )

            # Initialize segment progress for all segments of this video
            segments = video.segments.all()
            for seg in segments:
                UserShadowingSegment.objects.get_or_create(
                    user_video=user_video,
                    segment=seg,
                    defaults={"completed": False},
                )

        return user_video, created


class ShadowingProgressService:
    @staticmethod
    def calculate_progress(user_video: UserShadowingVideo) -> float:
        total = user_video.video.segments.count()
        if total == 0:
            return 0.0
        completed = UserShadowingSegment.objects.filter(
            user_video=user_video,
            completed=True,
        ).count()
        return round((completed / total) * 100.0, 2)

    @staticmethod
    def complete_segment(user, video_id, segment_id) -> Dict[str, Any]:
        video = get_object_or_404(ShadowingVideo, id=video_id)

        user_video = UserShadowingVideo.objects.filter(user=user, video=video).first()
        if not user_video:
            raise ValidationError("You must enroll in this video before completing segments.")

        # Cross-video segment lookup will 404 if segment does not belong to specified video
        segment = get_object_or_404(ShadowingSegment, id=segment_id, video=video)

        with transaction.atomic():
            uss, _ = UserShadowingSegment.objects.get_or_create(
                user_video=user_video,
                segment=segment,
            )

            # Idempotent: preserve first completed_at timestamp
            if not uss.completed:
                uss.completed = True
                uss.completed_at = timezone.now()
                uss.save(update_fields=["completed", "completed_at", "updated_at"])

            # Recalculate progress
            total = video.segments.count()
            completed_count = UserShadowingSegment.objects.filter(
                user_video=user_video,
                completed=True,
            ).count()
            progress = round((completed_count / total * 100.0), 2) if total > 0 else 0.0

            if total > 0 and completed_count == total:
                user_video.status = UserShadowingStatus.COMPLETED
                if not user_video.completed_at:
                    user_video.completed_at = timezone.now()
                user_video.save(update_fields=["status", "completed_at", "updated_at"])
            else:
                user_video.status = UserShadowingStatus.ACTIVE
                user_video.save(update_fields=["status", "updated_at"])

        return {
            "segment_id": str(segment.id),
            "completed": uss.completed,
            "completed_at": uss.completed_at,
            "completed_segments": completed_count,
            "total_segments": total,
            "percentage": progress,
            "video_status": user_video.status,
        }
