from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.shadowing.models import ShadowingVideo, VideoStatus
from apps.shadowing.services import ShadowingVideoService
from apps.shadowing.tasks import process_shadowing_video
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
class ServicesAndTasksTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="service_user", password="password123")

    @patch("apps.shadowing.services.process_shadowing_video.delay")
    def test_service_create_video_atomic(self, mock_celery):
        video_file = create_mock_video_file("lecture.mp4")
        data = {
            "title": "Software Architecture Lecture",
            "description": "Design patterns in Japanese",
            "level": "N2",
            "language": "ja",
            "metadata": {"tags": ["architecture", "clean-code"]},
        }

        with self.captureOnCommitCallbacks(execute=True):
            video, job = ShadowingVideoService.create_video(
                user=self.user,
                data=data,
                file_obj=video_file,
            )

        self.assertIsInstance(video, ShadowingVideo)
        self.assertEqual(video.title, "Software Architecture Lecture")
        self.assertEqual(video.status, VideoStatus.UPLOAD)
        self.assertEqual(video.metadata.get("job_id"), str(job.id))

        self.assertIsInstance(job, ProcessingJob)
        self.assertEqual(job.job_type, JobType.VIDEO_PROCESSING)
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertEqual(job.user, self.user)

        # Celery task dispatched with correct parameters
        mock_celery.assert_called_once_with(str(video.id), str(job.id))

    @patch("apps.shadowing.tasks.ShadowingProcessingPipeline.run")
    def test_celery_task_delegates_to_pipeline(self, mock_pipeline_run):
        mock_pipeline_run.return_value = {"status": "ready"}
        res = process_shadowing_video("fake-video-id", "fake-job-id")
        self.assertEqual(res, {"status": "ready"})
        mock_pipeline_run.assert_called_once_with(
            video_id="fake-video-id",
            job_id="fake-job-id",
        )

    @patch("apps.shadowing.tasks.ShadowingProcessingPipeline.run")
    def test_celery_task_reraises_exception(self, mock_pipeline_run):
        mock_pipeline_run.side_effect = RuntimeError("Worker failure")
        with self.assertRaises(RuntimeError):
            process_shadowing_video("fake-video-id", "fake-job-id")
