from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.jobs.models import JobStatus, JobType, ProcessingJob

User = get_user_model()


class ProcessingJobModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_create_processing_job(self):
        job = ProcessingJob.objects.create(
            user=self.user,
            job_type=JobType.PDF_PROCESSING,
        )
        self.assertIsNotNone(job.id)
        self.assertEqual(job.user, self.user)
        self.assertEqual(job.job_type, JobType.PDF_PROCESSING)

    def test_default_status_queued(self):
        job = ProcessingJob.objects.create(
            user=self.user,
            job_type=JobType.PDF_PROCESSING,
        )
        self.assertEqual(job.status, JobStatus.QUEUED)

    def test_progress_allows_null(self):
        job = ProcessingJob.objects.create(
            user=self.user,
            job_type=JobType.PDF_PROCESSING,
            progress=None,
        )
        job.full_clean()
        self.assertIsNone(job.progress)

    def test_progress_accepts_0_to_100(self):
        for val in [0, 50, 100]:
            job = ProcessingJob.objects.create(
                user=self.user,
                job_type=JobType.PDF_PROCESSING,
                progress=val,
            )
            job.full_clean()
            self.assertEqual(job.progress, val)

    def test_progress_rejects_invalid(self):
        with self.assertRaises(ValidationError):
            job = ProcessingJob(
                user=self.user,
                job_type=JobType.PDF_PROCESSING,
                progress=101,
            )
            job.save()

        with self.assertRaises(ValidationError):
            job = ProcessingJob(
                user=self.user,
                job_type=JobType.PDF_PROCESSING,
                progress=-1,
            )
            job.save()
