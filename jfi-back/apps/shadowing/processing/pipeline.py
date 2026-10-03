import logging
import os
import tempfile
from typing import Optional
from django.core.files.base import ContentFile

from apps.jobs.models import JobStatus, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.shadowing.models import ShadowingVideo, VideoStatus

from .exceptions import (
    AudioExtractionError,
    ShadowingProcessingError,
    TranscriptionError,
    TranscriptValidationError,
    VideoValidationError,
)
from .ffmpeg import FFmpegAudioExtractor
from .normalizer import TranscriptNormalizer
from .persistence import ShadowingPersistenceService
from .transcription import MockTranscriptionService, TranscriptionService
from .validator import TranscriptValidator, VideoValidator

logger = logging.getLogger(__name__)


class ShadowingProcessingPipeline:
    """
    Orchestrates end-to-end background processing of a ShadowingVideo:
    - FFmpeg audio extraction and metadata probing
    - Audio upload back to S3 / Cloudflare R2
    - Speech-to-text transcription
    - Transcript normalization and validation
    - Segment database persistence
    - ProcessingJob status and progress tracking
    """

    def __init__(
        self,
        audio_extractor: Optional[FFmpegAudioExtractor] = None,
        transcription_service: Optional[TranscriptionService] = None,
        persistence_service: Optional[ShadowingPersistenceService] = None,
    ):
        self.audio_extractor = audio_extractor or FFmpegAudioExtractor()
        self.transcription_service = transcription_service or MockTranscriptionService()
        self.persistence_service = persistence_service or ShadowingPersistenceService()

    def run(self, video_id: str, job_id: str):
        # 1. Load video and job
        try:
            video = ShadowingVideo.objects.get(id=video_id)
        except ShadowingVideo.DoesNotExist:
            logger.error("ShadowingVideo not found: %s", video_id)
            raise ShadowingProcessingError(f"ShadowingVideo {video_id} not found.")

        try:
            job = ProcessingJob.objects.get(id=job_id)
        except ProcessingJob.DoesNotExist:
            logger.error("ProcessingJob not found: %s", job_id)
            raise ShadowingProcessingError(f"ProcessingJob {job_id} not found.")

        # 2. Idempotency checks
        if job.status == JobStatus.COMPLETED:
            logger.info("Job %s is already completed. Skipping processing.", job_id)
            return {"status": "ready", "video_id": str(video.id), "already_completed": True}

        if job.status == JobStatus.CANCELLED:
            logger.info("Job %s was cancelled. Skipping processing.", job_id)
            return None

        temp_video_path: Optional[str] = None
        temp_audio_path: Optional[str] = None

        try:
            # 3. Mark job processing
            ProcessingJobService.mark_processing(
                job,
                current_step="starting",
                progress=0,
            )

            # 4. Mark video processing
            video.status = VideoStatus.PROCESSING
            video.error_message = ""
            video.save(update_fields=["status", "error_message", "updated_at"])

            # 5. Validate video
            ProcessingJobService.update_progress(
                job,
                progress=5,
                current_step="validating_video",
            )
            if not video.video_file:
                raise VideoValidationError("No video file attached to video record.")

            # Prepare local temporary file if video_file has no local filesystem path.
            # Remote storages (S3/R2) raise NotImplementedError on `.path`, even via hasattr().
            source_video_path = None
            try:
                local_path = video.video_file.path
            except (NotImplementedError, AttributeError, ValueError):
                local_path = None

            if local_path and os.path.exists(local_path):
                source_video_path = str(local_path)
            else:
                ext = os.path.splitext(video.video_file.name)[1] or ".mp4"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_vid:
                    temp_video_path = tmp_vid.name
                    with video.video_file.open("rb") as src:
                        for chunk in src.chunks():
                            tmp_vid.write(chunk)
                source_video_path = temp_video_path

            # Validate video file exists and is not empty
            if not os.path.exists(source_video_path) or os.path.getsize(source_video_path) == 0:
                raise VideoValidationError("Video file is missing or empty.")

            # 6. Extract audio with FFmpeg
            ProcessingJobService.update_progress(
                job,
                progress=15,
                current_step="extracting_audio",
            )
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
                temp_audio_path = tmp_audio.name

            self.audio_extractor.extract_audio(
                input_video_path=source_video_path,
                output_wav_path=temp_audio_path,
            )

            # 7. Store audio in R2/S3 storage
            ProcessingJobService.update_progress(
                job,
                progress=30,
                current_step="audio_extracted",
            )
            audio_filename = f"shadowing_audio_{video.id}.wav"
            with open(temp_audio_path, "rb") as af:
                video.audio_file.save(audio_filename, ContentFile(af.read()), save=False)

            # 8. Probe video for duration & technical metadata
            meta = self.audio_extractor.probe_video(source_video_path)
            if meta.get("duration_seconds"):
                video.duration_seconds = meta["duration_seconds"]
            if meta.get("file_size"):
                video.file_size = meta["file_size"]
            elif os.path.exists(source_video_path):
                video.file_size = os.path.getsize(source_video_path)

            video.metadata.update(meta)
            video.save(update_fields=["audio_file", "duration_seconds", "file_size", "metadata", "updated_at"])

            # 9. Transcribe audio
            ProcessingJobService.update_progress(
                job,
                progress=35,
                current_step="preparing_transcription",
            )
            ProcessingJobService.update_progress(
                job,
                progress=60,
                current_step="transcribing",
            )
            raw_segments = self.transcription_service.transcribe(
                audio_path=temp_audio_path,
                language=video.language or "ja",
            )

            # 10. Normalize transcript segments
            ProcessingJobService.update_progress(
                job,
                progress=85,
                current_step="normalizing_transcript",
            )
            normalized_segments = TranscriptNormalizer.normalize(raw_segments)

            # 11. Validate segments
            ProcessingJobService.update_progress(
                job,
                progress=90,
                current_step="validating_transcript",
            )
            TranscriptValidator.validate_segments(normalized_segments)

            # 12. Persist segments in database
            ProcessingJobService.update_progress(
                job,
                progress=95,
                current_step="saving_segments",
            )
            self.persistence_service.persist_segments(video, normalized_segments)

            # 13. Mark video ready
            video.status = VideoStatus.READY
            video.error_message = ""
            video.save(update_fields=["status", "error_message", "updated_at"])

            # 14. Mark job completed
            result_data = {
                "video_id": str(video.id),
                "segments_count": len(normalized_segments),
                "duration_seconds": video.duration_seconds,
            }
            ProcessingJobService.update_progress(job, progress=100, current_step="completed")
            ProcessingJobService.mark_completed(job, result=result_data)

            logger.info("Successfully processed shadowing video_id=%s, job_id=%s", video.id, job.id)
            return {"status": "ready", "video_id": str(video.id), "segments_count": len(normalized_segments)}

        except Exception as exc:
            # Map exception to safe user-facing message
            safe_error_msg = self._get_safe_error_message(exc)
            logger.exception("Pipeline failed for video_id=%s, job_id=%s: %s", video_id, job_id, str(exc))

            try:
                video.status = VideoStatus.FAILED
                video.error_message = safe_error_msg
                video.save(update_fields=["status", "error_message", "updated_at"])
            except Exception as e_video:
                logger.error("Failed to mark video failed: %s", str(e_video))

            try:
                ProcessingJobService.mark_failed(job, error_message=safe_error_msg)
            except Exception as e_job:
                logger.error("Failed to mark job failed: %s", str(e_job))

            # Re-raise so Celery records the failure
            raise

        finally:
            # Clean up all temporary files created during processing
            for p in [temp_video_path, temp_audio_path]:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError as e_clean:
                        logger.warning("Failed to remove temp file %s: %s", p, str(e_clean))

    @staticmethod
    def _get_safe_error_message(exc: Exception) -> str:
        if isinstance(exc, VideoValidationError):
            return "Video validation failed: invalid format or file."
        elif isinstance(exc, AudioExtractionError):
            return "Audio extraction failed."
        elif isinstance(exc, TranscriptionError):
            return "Audio transcription failed."
        elif isinstance(exc, TranscriptValidationError):
            return "Transcript validation failed."
        return "Video processing failed."
