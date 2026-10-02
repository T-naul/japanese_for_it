from django.db import transaction
from django.utils import timezone
from .models import JobStatus, ProcessingJob


class ProcessingJobService:
    @staticmethod
    def create_job(user, job_type, result=None):
        return ProcessingJob.objects.create(
            user=user,
            job_type=job_type,
            status=JobStatus.QUEUED,
            result=result or {},
        )

    @staticmethod
    @transaction.atomic
    def mark_processing(job, current_step="", progress=None):
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise ValueError(f"Cannot transition job from {job.status} to {JobStatus.PROCESSING}")

        if progress is not None and (progress < 0 or progress > 100):
            raise ValueError("Progress must be between 0 and 100.")

        job.status = JobStatus.PROCESSING
        if job.started_at is None:
            job.started_at = timezone.now()

        if current_step:
            job.current_step = current_step
        if progress is not None:
            job.progress = progress

        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def update_progress(job, progress=None, current_step=None):
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise ValueError(f"Cannot update progress for job with status {job.status}")

        if job.status != JobStatus.PROCESSING:
            raise ValueError(f"Cannot update progress for job with status {job.status}")

        if progress is not None and (progress < 0 or progress > 100):
            raise ValueError("Progress must be between 0 and 100.")

        if progress is not None:
            job.progress = progress
        if current_step is not None:
            job.current_step = current_step

        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def mark_completed(job, result=None):
        if job.status == JobStatus.COMPLETED:
            return job

        if job.status in [JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.QUEUED]:
            raise ValueError(f"Cannot transition job from {job.status} to {JobStatus.COMPLETED}")

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.completed_at = timezone.now()
        if result is not None:
            job.result = result

        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def mark_failed(job, error_message=""):
        if job.status == JobStatus.FAILED:
            return job

        if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]:
            raise ValueError(f"Cannot transition job from {job.status} to {JobStatus.FAILED}")

        job.status = JobStatus.FAILED
        job.error_message = str(error_message)
        job.completed_at = timezone.now()

        job.save()
        return job

    @staticmethod
    @transaction.atomic
    def mark_cancelled(job, reason=""):
        if job.status == JobStatus.CANCELLED:
            return job

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            raise ValueError(f"Cannot transition job from {job.status} to {JobStatus.CANCELLED}")

        job.status = JobStatus.CANCELLED
        if reason:
            job.error_message = str(reason)
        job.completed_at = timezone.now()

        job.save()
        return job
