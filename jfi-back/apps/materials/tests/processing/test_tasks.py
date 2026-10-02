import os
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from apps.jobs.models import JobStatus, JobType
from apps.jobs.services import ProcessingJobService
from apps.materials.models import LearningMaterial, MaterialStatus, MaterialType
from apps.materials.tasks import process_pdf_material
from .fixtures import write_synthetic_pdf_file

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="taskpipeuser", password="password123")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = os.path.join(self.temp_dir.name, "task_sample.pdf")
        write_synthetic_pdf_file(["第1課\n勉強します"], self.pdf_path)

        self.material = LearningMaterial.objects.create(
            title="Task PDF Material",
            material_type=MaterialType.PDF,
            metadata={"file_path": self.pdf_path},
        )
        self.job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_celery_task_calls_pipeline(self):
        res = process_pdf_material(str(self.material.id), str(self.job.id))

        self.assertEqual(res["status"], "ready")
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, MaterialStatus.READY)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.COMPLETED)

    def test_task_handles_exception_and_state_correctly(self):
        with patch("apps.materials.processing.pipeline.PDFProcessingPipeline.run", side_effect=RuntimeError("Pipeline failed")):
            with self.assertRaises(RuntimeError):
                process_pdf_material(str(self.material.id), str(self.job.id))

    def test_task_completed_job_early_return(self):
        ProcessingJobService.mark_processing(self.job)
        ProcessingJobService.mark_completed(self.job, result={"already": "done"})

        res = process_pdf_material(str(self.material.id), str(self.job.id))
        self.assertEqual(res, {"already": "done"})

    def test_task_cancelled_job_early_return(self):
        ProcessingJobService.mark_cancelled(self.job, reason="Cancelled")
        res = process_pdf_material(str(self.material.id), str(self.job.id))
        self.assertIsNone(res)
