from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.content.models import ContentStatus, Grammar, JLPTLevel, Vocabulary, WordType
from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.materials.models import (
    LearningMaterial,
    MaterialLesson,
    MaterialSection,
    MaterialSectionType,
    MaterialStatus,
    MaterialType,
    UserMaterial,
    UserMaterialLesson,
    UserMaterialStatus,
)
from apps.materials.tests.processing.fixtures import create_synthetic_pdf_bytes

User = get_user_model()


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class MaterialsAPITest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpassword123",
            email="admin@example.com",
        )
        self.user1 = User.objects.create_user(
            username="student1",
            password="userpassword123",
            email="student1@example.com",
        )
        self.user2 = User.objects.create_user(
            username="student2",
            password="userpassword123",
            email="student2@example.com",
        )

        self.pdf_bytes = create_synthetic_pdf_bytes(["第1課\nこんにちは", "第2課\n学生"])

        # Create sample ready material with lessons and sections
        self.ready_material = LearningMaterial.objects.create(
            title="Japanese for IT N4",
            description="Intermediate Japanese for IT",
            material_type=MaterialType.PDF,
            level="N4",
            language="ja",
            status=MaterialStatus.READY,
        )
        self.lesson1 = MaterialLesson.objects.create(
            material=self.ready_material,
            lesson_number=1,
            title="Lesson 1: Basics",
            page_start=1,
            page_end=2,
            content="Lesson 1 content",
        )
        self.lesson2 = MaterialLesson.objects.create(
            material=self.ready_material,
            lesson_number=2,
            title="Lesson 2: Advanced",
            page_start=3,
            page_end=4,
            content="Lesson 2 content",
        )

        # Sample vocabulary & grammar
        self.vocab = Vocabulary.objects.create(
            kanji="支度",
            hiragana="したく",
            meaning="preparation",
            word_type=WordType.NOUN,
            level=JLPTLevel.N4,
            status=ContentStatus.ACCEPTED,
        )
        self.grammar = Grammar.objects.create(
            pattern="～は～です",
            meaning="X is Y",
            level=JLPTLevel.N5,
            status=ContentStatus.ACCEPTED,
        )

        self.section1 = MaterialSection.objects.create(
            lesson=self.lesson1,
            order=1,
            title="Vocabulary Section",
            section_type=MaterialSectionType.VOCABULARY,
            vocabulary=self.vocab,
            content="Words list",
            data={"notes": "important"},
        )
        self.section2 = MaterialSection.objects.create(
            lesson=self.lesson1,
            order=2,
            title="Grammar Section",
            section_type=MaterialSectionType.GRAMMAR,
            grammar=self.grammar,
            content="Grammar explanation",
        )

        # Uploading material (non-ready)
        self.upload_material = LearningMaterial.objects.create(
            title="Draft Material",
            material_type=MaterialType.PDF,
            status=MaterialStatus.UPLOAD,
        )

    def get_uploaded_pdf(self, name="sample.pdf"):
        return SimpleUploadedFile(
            name,
            self.pdf_bytes,
            content_type="application/pdf",
        )

    # ==========================================================
    # 1. AUTHENTICATION & PERMISSIONS
    # ==========================================================

    def test_unauthenticated_list(self):
        res = self.client.get("/api/materials/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_unauthenticated_create(self):
        res = self.client.post("/api/materials/", {"title": "Test"}, format="multipart")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_non_admin_create_rejected(self):
        self.client.force_authenticate(user=self.user1)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Test", "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_update_rejected(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.patch(
            f"/api/materials/{self.ready_material.id}/",
            {"title": "Hacked Title"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_delete_rejected(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.delete(f"/api/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_isolation(self):
        # User 1 enrolls in material
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        # User 2 cannot see User 1's enrolled material in my materials
        self.client.force_authenticate(user=self.user2)
        res = self.client.get(f"/api/my/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ==========================================================
    # 2. CREATION
    # ==========================================================

    @patch("apps.materials.services.process_pdf_material.delay")
    def test_admin_creates_pdf(self, mock_celery):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()

        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(
                "/api/materials/",
                {
                    "title": "New IT Textbook",
                    "description": "IT Japanese Course",
                    "level": "N3",
                    "language": "ja",
                    "file": pdf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data
        self.assertIn("material", data)
        self.assertIn("job", data)
        self.assertEqual(data["material"]["title"], "New IT Textbook")
        self.assertEqual(data["material"]["status"], "upload")
        self.assertEqual(data["job"]["status"], "queued")

        # Verify Celery task was queued
        mock_celery.assert_called_once()
        mat_id = data["material"]["id"]
        job_id = data["job"]["job_id"]
        mock_celery.assert_called_with(mat_id, job_id)

    def test_missing_title(self):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "", "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", res.data)

    def test_missing_file(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.post(
            "/api/materials/",
            {"title": "No File Material"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_non_pdf(self):
        self.client.force_authenticate(user=self.admin_user)
        txt_file = SimpleUploadedFile("test.txt", b"plain text", content_type="text/plain")
        res = self.client.post(
            "/api/materials/",
            {"title": "Txt Material", "file": txt_file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_invalid_level(self):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Bad Level", "level": "N99", "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("level", res.data)

    def test_invalid_material_type(self):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Bad Type", "material_type": "unknown_type", "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("material_type", res.data)

    def test_status_cannot_be_client_controlled(self):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Try Ready", "status": "ready", "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", res.data)

    def test_page_count_cannot_be_client_controlled(self):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Try Page Count", "page_count": 999, "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("page_count", res.data)

    @patch("apps.materials.services.process_pdf_material.delay")
    def test_processing_job_created(self, mock_celery):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Check Job Creation", "file": pdf},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        job_id = res.data["job"]["job_id"]
        job = ProcessingJob.objects.get(id=job_id)
        self.assertEqual(job.job_type, JobType.PDF_PROCESSING)
        self.assertEqual(job.status, JobStatus.QUEUED)
        self.assertEqual(job.user, self.admin_user)

    @patch("apps.materials.services.process_pdf_material.delay")
    def test_celery_task_queued(self, mock_celery):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(
                "/api/materials/",
                {"title": "Check Celery Queue", "file": pdf},
                format="multipart",
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_celery.assert_called_once()

    @patch("apps.materials.services.process_pdf_material.delay")
    def test_request_does_not_run_pdf_pipeline_synchronously(self, mock_celery):
        self.client.force_authenticate(user=self.admin_user)
        pdf = self.get_uploaded_pdf()
        res = self.client.post(
            "/api/materials/",
            {"title": "Async Test", "file": pdf},
            format="multipart",
        )
        # Material remains in upload state, HTTP response returns immediately without extracting lessons
        self.assertEqual(res.data["material"]["status"], "upload")
        mat = LearningMaterial.objects.get(id=res.data["material"]["id"])
        self.assertEqual(mat.lessons.count(), 0)

    # ==========================================================
    # 3. PROCESSING STATUS
    # ==========================================================

    def test_queued_status(self):
        self.client.force_authenticate(user=self.admin_user)
        job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.PDF_PROCESSING,
            result={"material_id": str(self.ready_material.id)},
        )
        self.ready_material.metadata["job_id"] = str(job.id)
        self.ready_material.save()

        res = self.client.get(f"/api/materials/{self.ready_material.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "queued")
        self.assertEqual(res.data["job_id"], str(job.id))

    def test_processing_status(self):
        self.client.force_authenticate(user=self.admin_user)
        job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.PDF_PROCESSING,
            result={"material_id": str(self.ready_material.id)},
        )
        ProcessingJobService.mark_processing(job, current_step="extracting", progress=50)

        res = self.client.get(f"/api/materials/{self.ready_material.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "processing")
        self.assertEqual(res.data["progress"], 50)
        self.assertEqual(res.data["current_step"], "extracting")

    def test_completed_status(self):
        self.client.force_authenticate(user=self.admin_user)
        job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.PDF_PROCESSING,
            result={"material_id": str(self.ready_material.id)},
        )
        ProcessingJobService.mark_processing(job)
        ProcessingJobService.mark_completed(job, result={"done": True, "material_id": str(self.ready_material.id)})

        res = self.client.get(f"/api/materials/{self.ready_material.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "completed")
        self.assertEqual(res.data["progress"], 100)

    def test_failed_status(self):
        self.client.force_authenticate(user=self.admin_user)
        job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.PDF_PROCESSING,
            result={"material_id": str(self.ready_material.id)},
        )
        ProcessingJobService.mark_processing(job)
        ProcessingJobService.mark_failed(job, error_message="PDF parsing corrupted")

        res = self.client.get(f"/api/materials/{self.ready_material.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "failed")
        self.assertEqual(res.data["error_message"], "PDF parsing corrupted")

    def test_active_job_selection(self):
        self.client.force_authenticate(user=self.admin_user)
        # Create an old completed job
        old_job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.PDF_PROCESSING,
            result={"material_id": str(self.ready_material.id)},
        )
        ProcessingJobService.mark_processing(old_job)
        ProcessingJobService.mark_completed(old_job, result={"material_id": str(self.ready_material.id)})

        # Create a new active job
        active_job = ProcessingJobService.create_job(
            user=self.admin_user,
            job_type=JobType.PDF_PROCESSING,
            result={"material_id": str(self.ready_material.id)},
        )
        ProcessingJobService.mark_processing(active_job, current_step="parsing", progress=20)

        res = self.client.get(f"/api/materials/{self.ready_material.id}/processing/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Active job must be selected over older completed job
        self.assertEqual(res.data["job_id"], str(active_job.id))
        self.assertEqual(res.data["status"], "processing")

    # ==========================================================
    # 4. CRUD & MANAGEMENT
    # ==========================================================

    def test_admin_list(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/materials/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Admin sees both ready and upload materials
        ids = [m["id"] for m in res.data["results"]]
        self.assertIn(str(self.ready_material.id), ids)
        self.assertIn(str(self.upload_material.id), ids)

    def test_normal_user_list_only_ready(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get("/api/materials/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [m["id"] for m in res.data["results"]]
        self.assertIn(str(self.ready_material.id), ids)
        self.assertNotIn(str(self.upload_material.id), ids)

    def test_filtering(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/materials/?level=N4")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], str(self.ready_material.id))

    def test_search(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/materials/?search=Intermediate")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], str(self.ready_material.id))

    def test_detail(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], str(self.ready_material.id))
        self.assertEqual(res.data["title"], "Japanese for IT N4")

    def test_detail_non_ready_hidden_from_normal_user(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.upload_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_metadata_update(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f"/api/materials/{self.ready_material.id}/",
            {
                "title": "Updated Title",
                "description": "Updated Description",
                "level": "N3",
                "metadata": {"author": "Sensei"},
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.ready_material.refresh_from_db()
        self.assertEqual(self.ready_material.title, "Updated Title")
        self.assertEqual(self.ready_material.level, "N3")
        self.assertEqual(self.ready_material.metadata["author"], "Sensei")

    def test_invalid_update(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f"/api/materials/{self.ready_material.id}/",
            {"level": "INVALID"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_processing_fields_protected(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.patch(
            f"/api/materials/{self.ready_material.id}/",
            {"status": "failed", "page_count": 100},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_ready_material(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.delete(f"/api/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LearningMaterial.objects.filter(id=self.ready_material.id).exists())

    def test_delete_while_processing_rejected(self):
        self.client.force_authenticate(user=self.admin_user)
        self.ready_material.status = MaterialStatus.PROCESSING
        self.ready_material.save()

        res = self.client.delete(f"/api/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(LearningMaterial.objects.filter(id=self.ready_material.id).exists())

    @patch("apps.materials.services.process_pdf_material.delay")
    def test_safe_file_replacement(self, mock_celery):
        self.client.force_authenticate(user=self.admin_user)
        new_pdf = self.get_uploaded_pdf("new_file.pdf")

        res = self.client.patch(
            f"/api/materials/{self.ready_material.id}/",
            {"file": new_pdf, "title": "Replaced PDF Material"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.ready_material.refresh_from_db()
        self.assertEqual(self.ready_material.status, MaterialStatus.UPLOAD)
        # Previous lessons should have been safely cleared for fresh extraction
        self.assertEqual(self.ready_material.lessons.count(), 0)

    # ==========================================================
    # 5. LESSONS & SECTIONS
    # ==========================================================

    def test_lesson_list(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]["title"], "Lesson 1: Basics")
        self.assertFalse(res.data[0]["is_completed"])

    def test_lesson_ordering(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/")
        numbers = [l["lesson_number"] for l in res.data]
        self.assertEqual(numbers, [1, 2])

    def test_lesson_detail(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], str(self.lesson1.id))
        self.assertEqual(res.data["content"], "Lesson 1 content")
        self.assertEqual(res.data["sections_count"], 2)

    def test_cross_material_lesson_rejected(self):
        # Lesson from material B accessed via material A
        other_mat = LearningMaterial.objects.create(
            title="Other Material",
            material_type=MaterialType.PDF,
            status=MaterialStatus.READY,
        )
        other_lesson = MaterialLesson.objects.create(
            material=other_mat,
            lesson_number=1,
            title="Foreign Lesson",
        )

        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/{other_lesson.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_section_list(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/sections/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_section_ordering(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/sections/")
        orders = [s["order"] for s in res.data]
        self.assertEqual(orders, [1, 2])

    def test_vocabulary_grammar_references(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/sections/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sec1 = res.data[0]
        self.assertIsNotNone(sec1["vocabulary"])
        self.assertEqual(sec1["vocabulary"]["kanji"], "支度")
        sec2 = res.data[1]
        self.assertIsNotNone(sec2["grammar"])
        self.assertEqual(sec2["grammar"]["pattern"], "～は～です")

    # ==========================================================
    # 6. ENROLLMENT & USER PROGRESS
    # ==========================================================

    def test_enroll(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data["enrolled"])

        um = UserMaterial.objects.get(user=self.user1, material=self.ready_material)
        self.assertEqual(um.status, UserMaterialStatus.ACTIVE)
        self.assertEqual(um.lessons.count(), 2)

    def test_repeated_enrollment_idempotent(self):
        self.client.force_authenticate(user=self.user1)
        # First enroll
        res1 = self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Complete lesson 1
        um = UserMaterial.objects.get(user=self.user1, material=self.ready_material)
        uml = um.lessons.get(lesson=self.lesson1)
        uml.completed = True
        uml.save()

        # Second enroll: idempotent, returns 200, does not reset progress
        res2 = self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        uml.refresh_from_db()
        self.assertTrue(uml.completed)

    def test_lesson_progress_rows_created(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")
        um = UserMaterial.objects.get(user=self.user1, material=self.ready_material)
        lesson_ids = list(um.lessons.values_list("lesson_id", flat=True))
        self.assertIn(self.lesson1.id, lesson_ids)
        self.assertIn(self.lesson2.id, lesson_ids)

    def test_unavailable_material_rejected(self):
        # Non-admin user gets 404 (material is not ready and thus inaccessible)
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(f"/api/materials/{self.upload_material.id}/enroll/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Admin user gets 400 validation error (material is not ready)
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.post(f"/api/materials/{self.upload_material.id}/enroll/")
        self.assertEqual(res_admin.status_code, status.HTTP_400_BAD_REQUEST)

    def test_another_users_enrollment_invisible(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        self.client.force_authenticate(user=self.user2)
        res = self.client.get("/api/my/materials/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 0)

    # ==========================================================
    # 7. MY MATERIALS & PROGRESS
    # ==========================================================

    def test_my_materials_only(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        res = self.client.get("/api/my/materials/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["material"]["id"], str(self.ready_material.id))

    def test_progress_calculation(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        # Complete 1 out of 2 lessons -> 50%
        self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")

        res = self.client.get("/api/my/materials/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["progress"], 50.0)
        self.assertEqual(res.data["results"][0]["completed_lessons"], 1)
        self.assertEqual(res.data["results"][0]["total_lessons"], 2)

    def test_zero_lessons(self):
        empty_mat = LearningMaterial.objects.create(
            title="Empty Material",
            material_type=MaterialType.PDF,
            status=MaterialStatus.READY,
        )
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{empty_mat.id}/enroll/")

        res = self.client.get(f"/api/my/materials/{empty_mat.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["progress"], 0.0)
        self.assertEqual(res.data["total_lessons"], 0)

    def test_detail_includes_progress(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")
        res = self.client.get(f"/api/my/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["progress"], 0.0)
        self.assertEqual(len(res.data["lessons"]), 2)

    def test_owner_isolation_detail(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        self.client.force_authenticate(user=self.user2)
        res = self.client.get(f"/api/my/materials/{self.ready_material.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ==========================================================
    # 8. LESSON COMPLETION
    # ==========================================================

    def test_complete_lesson(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        res = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["completed"])
        self.assertEqual(res.data["material_progress"], 50.0)
        self.assertEqual(res.data["material_status"], "active")

    def test_repeated_completion_idempotent(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        res1 = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        completed_at_1 = res1.data["completed_at"]

        res2 = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["completed_at"], completed_at_1)

    def test_completed_at_stable(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        res1 = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        first_time = res1.data["completed_at"]
        self.assertIsNotNone(first_time)

        res2 = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.assertEqual(res2.data["completed_at"], first_time)

    def test_partial_progress(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        res = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.assertEqual(res.data["material_progress"], 50.0)
        self.assertEqual(res.data["material_status"], "active")

    def test_full_completion(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        res = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson2.id}/complete/")

        self.assertEqual(res.data["material_progress"], 100.0)
        self.assertEqual(res.data["material_status"], "completed")

    def test_user_material_becomes_completed(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson2.id}/complete/")

        um = UserMaterial.objects.get(user=self.user1, material=self.ready_material)
        self.assertEqual(um.status, UserMaterialStatus.COMPLETED)
        self.assertIsNotNone(um.completed_at)

    def test_user_material_completed_at_set(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson2.id}/complete/")

        um = UserMaterial.objects.get(user=self.user1, material=self.ready_material)
        self.assertTrue(isinstance(um.completed_at, timezone.datetime))

    def test_not_enrolled_rejected(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_material_lesson_completion_rejected(self):
        other_mat = LearningMaterial.objects.create(
            title="Other Mat",
            material_type=MaterialType.PDF,
            status=MaterialStatus.READY,
        )
        other_lesson = MaterialLesson.objects.create(
            material=other_mat,
            lesson_number=1,
            title="Other Lesson",
        )
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        res = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{other_lesson.id}/complete/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_another_user_progress_cannot_be_modified(self):
        # User 1 enrolls
        self.client.force_authenticate(user=self.user1)
        self.client.post(f"/api/materials/{self.ready_material.id}/enroll/")

        # User 2 tries to complete on User 1's progress
        self.client.force_authenticate(user=self.user2)
        res = self.client.post(f"/api/my/materials/{self.ready_material.id}/lessons/{self.lesson1.id}/complete/")
        # User 2 is not enrolled, so they cannot modify anything
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Verify User 1's lesson remains incomplete
        uml = UserMaterialLesson.objects.get(user_material__user=self.user1, lesson=self.lesson1)
        self.assertFalse(uml.completed)

    # ==========================================================
    # 9. GENERIC JOB STATUS
    # ==========================================================

    def test_generic_job_detail_admin(self):
        job = ProcessingJobService.create_job(
            user=self.user1,
            job_type=JobType.PDF_PROCESSING,
        )
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/jobs/{job.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["job_id"], str(job.id))

    def test_generic_job_detail_owner(self):
        job = ProcessingJobService.create_job(
            user=self.user1,
            job_type=JobType.PDF_PROCESSING,
        )
        self.client.force_authenticate(user=self.user1)
        res = self.client.get(f"/api/jobs/{job.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["job_id"], str(job.id))

    def test_generic_job_detail_forbidden(self):
        job = ProcessingJobService.create_job(
            user=self.user1,
            job_type=JobType.PDF_PROCESSING,
        )
        self.client.force_authenticate(user=self.user2)
        res = self.client.get(f"/api/jobs/{job.id}/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
