import os
import tempfile
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.jobs.models import JobStatus, JobType
from apps.jobs.services import ProcessingJobService
from apps.shadowing.models import ShadowingSegment, ShadowingVideo, VideoStatus
from apps.shadowing.processing.exceptions import (
    AudioExtractionError,
    TranscriptionError,
    TranscriptValidationError,
)
from apps.shadowing.processing.ffmpeg import FFmpegAudioExtractor
from apps.shadowing.processing.pipeline import ShadowingProcessingPipeline
from apps.shadowing.processing.transcription import MockTranscriptionService
from .fixtures import create_mock_video_file

User = get_user_model()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class PipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pipeline_user", password="password123")
        self.video = ShadowingVideo.objects.create(
            title="Japanese IT Standup",
            description="Daily scrum meeting dialogue",
            level="N3",
            language="ja",
            video_file=create_mock_video_file("scrum.mp4"),
        )
        self.job = ProcessingJobService.create_job(
            user=self.user,
            job_type=JobType.VIDEO_PROCESSING,
            result={"video_id": str(self.video.id)},
        )

        # Mock audio extractor
        self.mock_extractor = MagicMock(spec=FFmpegAudioExtractor)
        def fake_extract(input_video_path, output_wav_path, **kwargs):
            with open(output_wav_path, "wb") as f:
                f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00dummy audio wav bytes")
            return output_wav_path

        self.mock_extractor.extract_audio.side_effect = fake_extract
        self.mock_extractor.probe_video.return_value = {
            "duration_seconds": 12.34,
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
        }

        self.mock_transcriber = MockTranscriptionService([
            {"start_time": 0.0, "end_time": 3.0, "text": "おはようございます。本日のタスクを共有します。"},
            {"start_time": 3.2, "end_time": 6.5, "text": "APIの単体テストを実装中です。"},
        ])

        self.pipeline = ShadowingProcessingPipeline(
            audio_extractor=self.mock_extractor,
            transcription_service=self.mock_transcriber,
        )

    def test_pipeline_success_end_to_end(self):
        result = self.pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["segments_count"], 2)

        # Video state verification
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoStatus.READY)
        self.assertEqual(self.video.error_message, "")
        self.assertEqual(self.video.duration_seconds, 12.34)
        self.assertTrue(bool(self.video.audio_file))
        self.assertEqual(self.video.metadata.get("fps"), 30.0)

        # Job state verification
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.COMPLETED)
        self.assertEqual(self.job.progress, 100)
        self.assertEqual(self.job.current_step, "completed")
        self.assertEqual(self.job.result["segments_count"], 2)
        self.assertEqual(self.job.result["duration_seconds"], 12.34)

        # Segments verification
        segments = list(ShadowingSegment.objects.filter(video=self.video).order_by("sequence"))
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].sequence, 1)
        self.assertEqual(segments[0].text, "おはようございます。本日のタスクを共有します。")
        self.assertEqual(segments[1].sequence, 2)
        self.assertEqual(segments[1].text, "APIの単体テストを実装中です。")

    def test_pipeline_audio_extraction_failure(self):
        self.mock_extractor.extract_audio.side_effect = AudioExtractionError("Audio extraction failed.")

        with self.assertRaises(AudioExtractionError):
            self.pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoStatus.FAILED)
        self.assertEqual(self.video.error_message, "Audio extraction failed.")

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.FAILED)
        self.assertEqual(self.job.error_message, "Audio extraction failed.")

    def test_pipeline_transcription_failure(self):
        faulty_transcriber = MagicMock(spec=MockTranscriptionService)
        faulty_transcriber.transcribe.side_effect = TranscriptionError("Transcription failed.")
        pipeline = ShadowingProcessingPipeline(
            audio_extractor=self.mock_extractor,
            transcription_service=faulty_transcriber,
        )

        with self.assertRaises(TranscriptionError):
            pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoStatus.FAILED)
        self.assertEqual(self.video.error_message, "Audio transcription failed.")

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.FAILED)
        self.assertEqual(self.job.error_message, "Audio transcription failed.")

    def test_pipeline_empty_transcript_failure(self):
        empty_transcriber = MockTranscriptionService(predefined_segments=[])
        pipeline = ShadowingProcessingPipeline(
            audio_extractor=self.mock_extractor,
            transcription_service=empty_transcriber,
        )

        with self.assertRaises(TranscriptValidationError):
            pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoStatus.FAILED)
        self.assertEqual(self.video.error_message, "Transcript validation failed.")

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.FAILED)
        self.assertEqual(self.job.error_message, "Transcript validation failed.")

    def test_pipeline_completed_job_early_return(self):
        ProcessingJobService.mark_processing(self.job)
        ProcessingJobService.mark_completed(self.job, result={"already": "done"})

        result = self.pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))
        self.assertTrue(result.get("already_completed"))
        # Audio extractor should NOT be called
        self.mock_extractor.extract_audio.assert_not_called()

    def test_pipeline_cancelled_job_early_return(self):
        ProcessingJobService.mark_cancelled(self.job, reason="User cancelled")

        result = self.pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))
        self.assertIsNone(result)
        self.mock_extractor.extract_audio.assert_not_called()

    def test_pipeline_duplicate_run_does_not_duplicate_segments(self):
        # Run 1
        self.pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))
        self.assertEqual(self.video.segments.count(), 2)

        # Reset job for second run simulation
        self.job.status = JobStatus.QUEUED
        self.job.save(update_fields=["status"])

        # Run 2
        self.pipeline.run(video_id=str(self.video.id), job_id=str(self.job.id))
        self.assertEqual(self.video.segments.count(), 2)
