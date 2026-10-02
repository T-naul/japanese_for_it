from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.jobs.tasks import run_demo_job

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class DemoTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="taskuser", password="password123")

    def test_demo_task_completes(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        res = run_demo_job(str(job.id))
        job.refresh_from_db()

        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertEqual(job.progress, 100)
        self.assertIsNotNone(job.started_at)
        self.assertIsNotNone(job.completed_at)
        self.assertEqual(job.result, {"status": "success", "message": "Demo job completed successfully"})
        self.assertIn("completed", res)

    def test_demo_task_failure_marks_failed(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)

        with patch("apps.jobs.services.ProcessingJobService.update_progress", side_effect=RuntimeError("Simulated processing error")):
            with self.assertRaises(RuntimeError):
                run_demo_job(str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.error_message, "Simulated processing error")
        self.assertIsNotNone(job.completed_at)

    def test_completed_job_not_processed_again(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        ProcessingJobService.mark_processing(job)
        ProcessingJobService.mark_completed(job, result={"initial": "data"})

        res = run_demo_job(str(job.id))
        job.refresh_from_db()

        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertEqual(job.result, {"initial": "data"})
        self.assertIn("already in terminal status", res)

    def test_failed_job_not_processed_again(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        ProcessingJobService.mark_processing(job)
        ProcessingJobService.mark_failed(job, error_message="Original failure")

        res = run_demo_job(str(job.id))
        job.refresh_from_db()

        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.error_message, "Original failure")
        self.assertIn("already in terminal status", res)

    def test_duplicate_processing_is_safe(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        ProcessingJobService.mark_processing(job, current_step="External processing", progress=25)

        res = run_demo_job(str(job.id))
        job.refresh_from_db()

        self.assertEqual(job.status, JobStatus.PROCESSING)
        self.assertEqual(job.progress, 25)
        self.assertEqual(job.current_step, "External processing")
        self.assertIn("is already processing", res)
