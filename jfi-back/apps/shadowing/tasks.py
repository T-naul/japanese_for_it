import logging
from celery import shared_task
from .processing.pipeline import ShadowingProcessingPipeline

logger = logging.getLogger(__name__)


@shared_task
def process_shadowing_video(video_id: str, job_id: str):
    """
    Celery task that delegates background processing of video shadowing
    to the ShadowingProcessingPipeline.
    """
    logger.info("Starting process_shadowing_video task for video_id=%s, job_id=%s", video_id, job_id)
    try:
        pipeline = ShadowingProcessingPipeline()
        return pipeline.run(video_id=video_id, job_id=job_id)
    except Exception as exc:
        logger.error("process_shadowing_video failed for video_id=%s, job_id=%s: %s", video_id, job_id, str(exc))
        raise
