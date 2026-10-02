from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.jobs.models import JobStatus, JobType
from apps.jobs.services import ProcessingJobService

User = get_user_model()


class ProcessingJobServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="serviceuser", password="password123")

    def test_create_processing_job(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertEqual(job.user, self.user)

    def test_mark_processing(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job, current_step="Step 1", progress=10)
        self.assertEqual(job.status, JobStatus.PROCESSING)
        self.assertEqual(job.current_step, "Step 1")
        self.assertEqual(job.progress, 10)

    def test_mark_processing_sets_started_at(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        self.assertIsNone(job.started_at)
        job = ProcessingJobService.mark_processing(job)
        self.assertIsNotNone(job.started_at)

    def test_update_progress(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job, progress=10, current_step="Step 1")
        job = ProcessingJobService.update_progress(job, progress=40, current_step="Step 2")
        self.assertEqual(job.progress, 40)
        self.assertEqual(job.current_step, "Step 2")

    def test_mark_completed_sets_100(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job)
        job = ProcessingJobService.mark_completed(job, result={"res": "ok"})
        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertEqual(job.progress, 100)
        self.assertEqual(job.result, {"res": "ok"})

    def test_mark_completed_sets_completed_at(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job)
        self.assertIsNone(job.completed_at)
        job = ProcessingJobService.mark_completed(job)
        self.assertIsNotNone(job.completed_at)

    def test_mark_failed(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job)
        job = ProcessingJobService.mark_failed(job, error_message="Something went wrong")
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.error_message, "Something went wrong")
        self.assertIsNotNone(job.completed_at)

    def test_mark_cancelled(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_cancelled(job, reason="User cancelled")
        self.assertEqual(job.status, JobStatus.CANCELLED)
        self.assertEqual(job.error_message, "User cancelled")
        self.assertIsNotNone(job.completed_at)

    def test_cannot_update_completed(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job)
        job = ProcessingJobService.mark_completed(job)

        with self.assertRaises(ValueError):
            ProcessingJobService.update_progress(job, progress=50)

        with self.assertRaises(ValueError):
            ProcessingJobService.mark_processing(job)

    def test_cannot_update_failed(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_processing(job)
        job = ProcessingJobService.mark_failed(job, error_message="Error")

        with self.assertRaises(ValueError):
            ProcessingJobService.update_progress(job, progress=50)

        with self.assertRaises(ValueError):
            ProcessingJobService.mark_completed(job)

    def test_cannot_update_cancelled(self):
        job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        job = ProcessingJobService.mark_cancelled(job, reason="Cancelled")

        with self.assertRaises(ValueError):
            ProcessingJobService.update_progress(job, progress=50)

        with self.assertRaises(ValueError):
            ProcessingJobService.mark_processing(job)
