import os
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.materials.models import LearningMaterial, MaterialLesson, MaterialSection, MaterialStatus, MaterialType
from apps.materials.processing.pipeline import PDFProcessingPipeline
from .fixtures import write_synthetic_pdf_file

User = get_user_model()


class PipelineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pipeuser", password="password123")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = os.path.join(self.temp_dir.name, "sample.pdf")
        write_synthetic_pdf_file(
            [
                "第1課\nこんにちは\n学生\n支度\nしたく",
                "～は～です\n私は学生です。",
            ],
            self.pdf_path,
        )

        self.material = LearningMaterial.objects.create(
            title="Sample PDF Material",
            material_type=MaterialType.PDF,
            metadata={"file_path": self.pdf_path},
        )
        self.job = ProcessingJobService.create_job(self.user, JobType.PDF_PROCESSING)
        self.pipeline = PDFProcessingPipeline()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_successful_pipeline(self):
        result = self.pipeline.run(self.material.id, self.job.id)

        self.assertEqual(result["status"], "ready")
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, MaterialStatus.READY)
        self.assertEqual(self.material.page_count, 2)

        # Check created lesson & sections
        lessons = MaterialLesson.objects.filter(material=self.material)
        self.assertEqual(lessons.count(), 1)
        sections = MaterialSection.objects.filter(lesson=lessons.first())
        self.assertTrue(sections.count() >= 1)

    def test_material_becomes_ready(self):
        self.pipeline.run(self.material.id, self.job.id)
        self.material.refresh_from_db()
        self.assertEqual(self.material.status, MaterialStatus.READY)
        self.assertEqual(self.material.error_message, "")

    def test_job_becomes_completed(self):
        self.pipeline.run(self.material.id, self.job.id)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.COMPLETED)
        self.assertEqual(self.job.progress, 100)
        self.assertIsNotNone(self.job.started_at)
        self.assertIsNotNone(self.job.completed_at)

    def test_progress_updates(self):
        with patch.object(ProcessingJobService, "update_progress", wraps=ProcessingJobService.update_progress) as mock_update:
            self.pipeline.run(self.material.id, self.job.id)
            # Verify update_progress was called multiple times during steps
            self.assertTrue(mock_update.call_count >= 5)

    def test_failure_marks_material_failed(self):
        # Trigger an error during extraction
        with patch("apps.materials.processing.extractor.DummyContentExtractor.extract", side_effect=RuntimeError("Extractor crashed")):
            with self.assertRaises(RuntimeError):
                self.pipeline.run(self.material.id, self.job.id)

        self.material.refresh_from_db()
        self.assertEqual(self.material.status, MaterialStatus.FAILED)
        self.assertIn("Extractor crashed", self.material.error_message)

    def test_failure_marks_job_failed(self):
        with patch("apps.materials.processing.extractor.DummyContentExtractor.extract", side_effect=RuntimeError("Extractor crashed")):
            with self.assertRaises(RuntimeError):
                self.pipeline.run(self.material.id, self.job.id)

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.FAILED)
        self.assertIn("Extractor crashed", self.job.error_message)
        self.assertIsNotNone(self.job.completed_at)

    def test_cancelled_job_does_not_process(self):
        ProcessingJobService.mark_cancelled(self.job, reason="User cancelled early")
        res = self.pipeline.run(self.material.id, self.job.id)

        self.assertIsNone(res)
        self.material.refresh_from_db()
        # Material should remain upload (not processed)
        self.assertEqual(self.material.status, MaterialStatus.UPLOAD)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.CANCELLED)

    def test_completed_job_idempotent(self):
        # Run first time
        self.pipeline.run(self.material.id, self.job.id)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.COMPLETED)
        original_result = self.job.result

        # Run second time
        res = self.pipeline.run(self.material.id, self.job.id)
        self.assertEqual(res, original_result)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.COMPLETED)
