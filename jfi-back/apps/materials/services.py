import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.jobs.models import JobStatus, JobType, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.materials.models import (
    LearningMaterial,
    MaterialLesson,
    MaterialSection,
    MaterialStatus,
    MaterialType,
    UserMaterial,
    UserMaterialLesson,
    UserMaterialStatus,
)
from apps.materials.tasks import process_pdf_material

logger = logging.getLogger(__name__)


class ConflictError(APIException):
    status_code = 409
    default_detail = "Conflict with current resource state."
    default_code = "conflict"


def validate_pdf_file(file_obj):
    if not file_obj:
        raise ValidationError({"file": "A PDF file is required."})

    # Validate filename extension
    name = getattr(file_obj, "name", "") or ""
    if not name.lower().endswith(".pdf"):
        raise ValidationError({"file": "File must have a .pdf extension."})

    # Validate file size
    size = getattr(file_obj, "size", 0)
    if size <= 0:
        raise ValidationError({"file": "File is empty."})

    # Validate PDF magic header
    try:
        header = file_obj.read(1024)
        file_obj.seek(0)
        if b"%PDF" not in header:
            raise ValidationError({"file": "Invalid PDF format: %PDF header missing."})
    except Exception as exc:
        raise ValidationError({"file": f"Could not read uploaded file: {exc}"})


class MaterialService:
    @staticmethod
    def get_materials_queryset(user):
        """
        Admins can view all materials.
        Normal users can only view materials that are ready.
        """
        qs = LearningMaterial.objects.all()
        if not (user and user.is_staff):
            qs = qs.filter(status=MaterialStatus.READY)
        return qs

    @staticmethod
    def create_material(user, data, file_obj) -> tuple[LearningMaterial, ProcessingJob]:
        title = data.get("title", "").strip()
        if not title:
            raise ValidationError({"title": "Title is required and cannot be empty."})

        validate_pdf_file(file_obj)

        material_type = data.get("material_type", MaterialType.PDF)
        if material_type not in MaterialType.values:
            raise ValidationError({"material_type": f"Invalid material_type '{material_type}'."})

        level = data.get("level", "")
        if level and level not in ["N5", "N4", "N3", "N2", "N1"]:
            raise ValidationError({"level": f"Invalid JLPT level '{level}'."})

        language = data.get("language", "ja")
        description = data.get("description", "")
        metadata = dict(data.get("metadata", {}))

        with transaction.atomic():
            material = LearningMaterial.objects.create(
                title=title,
                description=description,
                material_type=material_type,
                level=level,
                language=language,
                file=file_obj,
                file_size=file_obj.size,
                status=MaterialStatus.UPLOAD,
                metadata=metadata,
            )

            # Create ProcessingJob
            job = ProcessingJobService.create_job(
                user=user,
                job_type=JobType.PDF_PROCESSING,
                result={"material_id": str(material.id)},
            )
            material.metadata["job_id"] = str(job.id)
            material.save(update_fields=["metadata", "updated_at"])

            # Queue Celery processing after commit
            transaction.on_commit(
                lambda: process_pdf_material.delay(str(material.id), str(job.id))
            )

        logger.info("Created material_id=%s with job_id=%s", material.id, job.id)
        return material, job

    @staticmethod
    def update_material(material: LearningMaterial, user, data, file_obj=None) -> tuple[LearningMaterial, ProcessingJob | None]:
        # Disallow client mutation of server-controlled fields
        for field in ["status", "page_count", "error_message", "id", "created_at", "updated_at"]:
            if field in data:
                raise ValidationError({field: f"Field '{field}' cannot be modified directly."})

        if "title" in data:
            title = data["title"].strip()
            if not title:
                raise ValidationError({"title": "Title cannot be empty."})
            material.title = title

        if "description" in data:
            material.description = data["description"]

        if "level" in data:
            level = data["level"]
            if level and level not in ["N5", "N4", "N3", "N2", "N1"]:
                raise ValidationError({"level": f"Invalid JLPT level '{level}'."})
            material.level = level

        if "language" in data:
            material.language = data["language"]

        if "metadata" in data and isinstance(data["metadata"], dict):
            # Preserve internal job_id if present
            job_id = material.metadata.get("job_id")
            material.metadata = dict(data["metadata"])
            if job_id:
                material.metadata["job_id"] = job_id

        new_job = None
        if file_obj:
            if material.status == MaterialStatus.PROCESSING:
                raise ConflictError("Cannot replace file while material is currently processing.")

            validate_pdf_file(file_obj)

            with transaction.atomic():
                # Clean up stale extracted lessons/sections
                material.lessons.all().delete()

                material.file = file_obj
                material.file_size = file_obj.size
                material.page_count = None
                material.status = MaterialStatus.UPLOAD
                material.error_message = ""

                # Create new processing job
                new_job = ProcessingJobService.create_job(
                    user=user,
                    job_type=JobType.PDF_PROCESSING,
                    result={"material_id": str(material.id)},
                )
                material.metadata["job_id"] = str(new_job.id)
                material.save()

                transaction.on_commit(
                    lambda: process_pdf_material.delay(str(material.id), str(new_job.id))
                )
        else:
            material.save()

        return material, new_job

    @staticmethod
    def delete_material(material: LearningMaterial):
        if material.status == MaterialStatus.PROCESSING:
            raise ConflictError("Cannot delete material while it is currently processing.")
        material.delete()


class ProcessingService:
    @staticmethod
    def get_material_processing_status(material: LearningMaterial) -> dict | None:
        """
        Returns active queued/processing job first, otherwise latest job for the material.
        """
        # Look for jobs associated with this material
        jobs = ProcessingJob.objects.filter(
            result__material_id=str(material.id)
        ).order_by("-created_at")

        job = None
        for j in jobs:
            if j.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                job = j
                break

        if not job:
            job = jobs.first()

        if not job and material.metadata.get("job_id"):
            try:
                job = ProcessingJob.objects.get(id=material.metadata["job_id"])
            except ProcessingJob.DoesNotExist:
                job = None

        if not job:
            return None

        return {
            "job_id": str(job.id),
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "error_message": job.error_message or None,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }

    @staticmethod
    def get_job_detail(job_id, user) -> ProcessingJob:
        job = get_object_or_404(ProcessingJob, id=job_id)
        if not (user and (user.is_staff or job.user == user)):
            raise PermissionDenied("You do not have permission to view this job.")
        return job


class EnrollmentService:
    @staticmethod
    def enroll_user(user, material: LearningMaterial) -> tuple[UserMaterial, bool]:
        if material.status != MaterialStatus.READY:
            raise ValidationError("Material is not ready for enrollment.")

        with transaction.atomic():
            user_material, created = UserMaterial.objects.get_or_create(
                user=user,
                material=material,
                defaults={
                    "status": UserMaterialStatus.ACTIVE,
                    "started_at": timezone.now(),
                },
            )

            # Initialize UserMaterialLesson for all current lessons if not present
            lessons = material.lessons.all()
            for lesson in lessons:
                UserMaterialLesson.objects.get_or_create(
                    user_material=user_material,
                    lesson=lesson,
                    defaults={"completed": False},
                )

        return user_material, created


class LessonService:
    @staticmethod
    def get_lessons_for_material(material: LearningMaterial, user=None):
        lessons = material.lessons.all().order_by("lesson_number")
        completed_ids = set()
        if user and user.is_authenticated:
            completed_ids = set(
                UserMaterialLesson.objects.filter(
                    user_material__user=user,
                    user_material__material=material,
                    completed=True,
                ).values_list("lesson_id", flat=True)
            )

        for lesson in lessons:
            lesson.is_completed = lesson.id in completed_ids

        return lessons

    @staticmethod
    def get_lesson_detail(material: LearningMaterial, lesson_id, user=None):
        lesson = get_object_or_404(MaterialLesson, id=lesson_id, material=material)
        lesson.is_completed = False
        if user and user.is_authenticated:
            uml = UserMaterialLesson.objects.filter(
                user_material__user=user,
                user_material__material=material,
                lesson=lesson,
            ).first()
            if uml:
                lesson.is_completed = uml.completed

        return lesson

    @staticmethod
    def get_sections_for_lesson(material: LearningMaterial, lesson_id):
        lesson = get_object_or_404(MaterialLesson, id=lesson_id, material=material)
        return (
            lesson.sections.all()
            .order_by("order")
            .select_related("vocabulary", "grammar")
        )

    @staticmethod
    def calculate_progress(user_material: UserMaterial) -> float:
        total = user_material.material.lessons.count()
        if total == 0:
            return 0.0
        completed = UserMaterialLesson.objects.filter(
            user_material=user_material,
            completed=True,
        ).count()
        return round((completed / total) * 100.0, 2)

    @staticmethod
    def complete_lesson(user, material_id, lesson_id) -> dict:
        material = get_object_or_404(LearningMaterial, id=material_id)

        user_material = UserMaterial.objects.filter(user=user, material=material).first()
        if not user_material:
            raise ValidationError("You must enroll in this material before completing lessons.")

        lesson = get_object_or_404(MaterialLesson, id=lesson_id, material=material)

        with transaction.atomic():
            uml, _ = UserMaterialLesson.objects.get_or_create(
                user_material=user_material,
                lesson=lesson,
            )

            if not uml.completed:
                uml.completed = True
                uml.completed_at = timezone.now()
                uml.save(update_fields=["completed", "completed_at"])

            # Recalculate progress
            total = material.lessons.count()
            completed_count = UserMaterialLesson.objects.filter(
                user_material=user_material,
                completed=True,
            ).count()
            progress = (completed_count / total * 100.0) if total > 0 else 0.0

            if total > 0 and completed_count == total:
                user_material.status = UserMaterialStatus.COMPLETED
                if not user_material.completed_at:
                    user_material.completed_at = timezone.now()
                user_material.save(update_fields=["status", "completed_at", "updated_at"])
            else:
                user_material.status = UserMaterialStatus.ACTIVE
                user_material.save(update_fields=["status", "updated_at"])

        return {
            "lesson_id": str(lesson.id),
            "completed": uml.completed,
            "completed_at": uml.completed_at,
            "material_progress": round(progress, 2),
            "material_status": user_material.status,
        }
