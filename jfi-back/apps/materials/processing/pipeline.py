import logging
import os
from apps.jobs.models import JobStatus, ProcessingJob
from apps.jobs.services import ProcessingJobService
from apps.materials.models import LearningMaterial, MaterialStatus
from .chunker import DocumentChunker
from .exceptions import PDFProcessingError
from .extractor import DummyContentExtractor
from .matcher import ContentMatcher
from .ocr import NullOCRProvider, apply_ocr_if_needed
from .pdf_parser import PDFParser
from .persistence import MaterialPersistenceService
from .validator import ExtractionValidator

logger = logging.getLogger(__name__)


class PDFProcessingPipeline:
    def __init__(
        self,
        parser=None,
        ocr_provider=None,
        chunker=None,
        extractor=None,
        validator=None,
        matcher=None,
        persistence=None,
        job_service=None,
    ):
        self.parser = parser or PDFParser()
        self.ocr_provider = ocr_provider or NullOCRProvider()
        self.chunker = chunker or DocumentChunker()
        self.extractor = extractor or DummyContentExtractor()
        self.validator = validator or ExtractionValidator()
        self.matcher = matcher or ContentMatcher()
        self.persistence = persistence or MaterialPersistenceService(matcher=self.matcher)
        self.job_service = job_service or ProcessingJobService()

    def run(self, material_id, job_id=None):
        logger.info("Starting PDF pipeline for material_id=%s, job_id=%s", material_id, job_id)

        # 1. Load Material
        try:
            material = LearningMaterial.objects.get(id=material_id)
        except LearningMaterial.DoesNotExist:
            logger.error("LearningMaterial with id=%s not found", material_id)
            raise PDFProcessingError(f"LearningMaterial {material_id} does not exist")

        # 2. Load Job if provided
        job = None
        if job_id:
            try:
                job = ProcessingJob.objects.get(id=job_id)
            except ProcessingJob.DoesNotExist:
                logger.error("ProcessingJob with id=%s not found", job_id)
                raise PDFProcessingError(f"ProcessingJob {job_id} does not exist")

            # 3. Idempotency checks
            if job.status == JobStatus.COMPLETED:
                logger.info("Job %s is already completed. Skipping processing.", job_id)
                return job.result

            if job.status == JobStatus.CANCELLED:
                logger.info("Job %s is cancelled. Aborting processing.", job_id)
                return None

        # If material is already ready and no active job, avoid unnecessary reprocessing
        if material.status == MaterialStatus.READY and not job:
            logger.info("Material %s is already ready.", material_id)
            return material

        # 4. Mark Job & Material as PROCESSING
        if job:
            self.job_service.mark_processing(job, current_step="starting", progress=0)

        material.status = MaterialStatus.PROCESSING
        material.error_message = ""
        material.save(update_fields=["status", "error_message", "updated_at"])

        try:
            # 5. Resolve file path
            # Remote storages (S3/R2) don't support `.path` and raise
            # NotImplementedError when it's accessed — even via hasattr().
            file_path = None
            temp_file_created = False
            if material.file:
                try:
                    file_path = material.file.path
                except (NotImplementedError, AttributeError, ValueError):
                    file_path = None

            if (not file_path or not os.path.exists(file_path)) and material.metadata:
                meta_path = material.metadata.get("file_path")
                if meta_path and os.path.exists(meta_path):
                    file_path = meta_path

            if (not file_path or not os.path.exists(file_path)) and material.file:
                import tempfile
                try:
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        file_path = tmp.name
                        temp_file_created = True
                        with material.file.open("rb") as src:
                            for chunk in src.chunks():
                                tmp.write(chunk)
                except Exception as exc:
                    logger.warning("Failed to download material file to tempfile: %s", exc)
                    raise PDFProcessingError(
                        f"Cannot download file for material {material_id} from storage."
                    ) from exc

            if not file_path or not os.path.exists(file_path):
                raise PDFProcessingError(f"File for material {material_id} does not exist: {file_path}")

            # 6. Reading PDF
            if job:
                self.job_service.update_progress(job, progress=10, current_step="reading_pdf")

            # 7. Parsing pages
            if job:
                self.job_service.update_progress(job, progress=25, current_step="parsing_pages")
            pages = self.parser.parse(file_path)

            material.page_count = len(pages)
            material.save(update_fields=["page_count", "updated_at"])

            # 8. OCR fallback if needed
            pages = apply_ocr_if_needed(pages, self.ocr_provider)

            # 9. Chunking
            if job:
                self.job_service.update_progress(job, progress=40, current_step="chunking")
            chunks = self.chunker.chunk(pages)

            # 10. Extract, Validate, Match, Persist
            total_chunks = len(chunks)
            for idx, chunk in enumerate(chunks):
                chunk_index = idx + 1
                base_progress = 50
                range_progress = 20
                extract_progress = base_progress + int((idx / max(total_chunks, 1)) * range_progress)

                # Extract
                if job:
                    self.job_service.update_progress(
                        job, progress=extract_progress, current_step=f"extracting (chunk {chunk_index}/{total_chunks})"
                    )
                extracted_data = self.extractor.extract(chunk)

                # Validate
                if job:
                    self.job_service.update_progress(
                        job, progress=70, current_step=f"validating (chunk {chunk_index}/{total_chunks})"
                    )
                validated_data = self.validator.validate(extracted_data)

                # Match
                if job:
                    self.job_service.update_progress(
                        job, progress=80, current_step=f"matching (chunk {chunk_index}/{total_chunks})"
                    )

                # Save / Persist
                if job:
                    self.job_service.update_progress(
                        job, progress=90, current_step=f"saving (chunk {chunk_index}/{total_chunks})"
                    )
                self.persistence.persist(
                    material=material,
                    extraction_data=validated_data,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                )

            # 11. Material READY
            material.status = MaterialStatus.READY
            material.error_message = ""
            material.save(update_fields=["status", "error_message", "updated_at"])

            # 12. Job COMPLETED
            result_payload = {
                "material_id": str(material.id),
                "total_chunks": total_chunks,
                "status": "ready",
            }
            if job:
                self.job_service.mark_completed(job, result=result_payload)

            logger.info("PDF pipeline completed successfully for material_id=%s", material_id)
            return result_payload

        except Exception as exc:
            logger.exception("PDF pipeline failed for material_id=%s, job_id=%s: %s", material_id, job_id, exc)
            err_msg = str(exc)
            material.status = MaterialStatus.FAILED
            material.error_message = err_msg
            material.save(update_fields=["status", "error_message", "updated_at"])

            if job:
                self.job_service.mark_failed(job, error_message=err_msg)

            raise
        finally:
            if temp_file_created and file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

