from celery import shared_task
from .models import JobStatus, ProcessingJob
from .services import ProcessingJobService


@shared_task
def run_demo_job(job_id):
    try:
        job = ProcessingJob.objects.get(id=job_id)
    except ProcessingJob.DoesNotExist:
        return f"Job {job_id} not found"

    # Idempotency checks
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        return f"Job {job_id} already in terminal status {job.status}"

    if job.status == JobStatus.PROCESSING:
        return f"Job {job_id} is already processing"

    try:
        ProcessingJobService.mark_processing(job, current_step="Initializing demo job", progress=10)
        ProcessingJobService.update_progress(job, progress=50, current_step="Processing demo step")
        ProcessingJobService.mark_completed(
            job,
            result={"status": "success", "message": "Demo job completed successfully"},
        )
        return f"Job {job_id} completed"
    except Exception as exc:
        ProcessingJobService.mark_failed(job, error_message=str(exc))
        raise
