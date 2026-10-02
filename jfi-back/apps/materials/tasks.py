import logging
from celery import shared_task
from apps.jobs.models import JobStatus, ProcessingJob
from apps.materials.processing.pipeline import PDFProcessingPipeline

logger = logging.getLogger(__name__)


@shared_task
def process_pdf_material(material_id, job_id=None):
    """
    Celery task to run the PDF processing pipeline for a LearningMaterial.
    """
    # Quick idempotency checks before invoking pipeline
    if job_id:
        try:
            job = ProcessingJob.objects.get(id=job_id)
            if job.status == JobStatus.COMPLETED:
                logger.info("Job %s is already completed. Returning result.", job_id)
                return job.result
            if job.status == JobStatus.CANCELLED:
                logger.info("Job %s is cancelled. Not processing.", job_id)
                return None
        except ProcessingJob.DoesNotExist:
            pass

    pipeline = PDFProcessingPipeline()
    try:
        return pipeline.run(material_id=material_id, job_id=job_id)
    except Exception as exc:
        logger.exception("Task process_pdf_material failed: %s", exc)
        raise
