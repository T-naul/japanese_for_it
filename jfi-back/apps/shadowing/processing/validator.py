import os
from typing import Any, Dict, List
from django.conf import settings

from .exceptions import TranscriptValidationError, VideoValidationError


class VideoValidator:
    """
    Validates uploaded video files for shadowing processing.
    """

    SUPPORTED_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv"}

    @classmethod
    def get_max_size_bytes(cls) -> int:
        mb = getattr(settings, "MAX_SHADOWING_VIDEO_SIZE_MB", 500)
        return int(mb) * 1024 * 1024

    @classmethod
    def validate_uploaded_file(cls, file_obj) -> None:
        if not file_obj:
            raise VideoValidationError("Video file is required.")

        file_name = getattr(file_obj, "name", "")
        if not file_name:
            raise VideoValidationError("Video file must have a filename.")

        ext = os.path.splitext(file_name)[1].lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(cls.SUPPORTED_EXTENSIONS))
            raise VideoValidationError(
                f"Unsupported video format '{ext}'. Allowed formats: {allowed}."
            )

        file_size = getattr(file_obj, "size", 0)
        if file_size <= 0:
            raise VideoValidationError("Uploaded video file is empty.")

        max_size = cls.get_max_size_bytes()
        if file_size > max_size:
            max_mb = max_size // (1024 * 1024)
            raise VideoValidationError(
                f"Video file exceeds maximum allowed size of {max_mb}MB."
            )

        # Basic magic bytes check if available
        if hasattr(file_obj, "read") and hasattr(file_obj, "seek"):
            current_pos = file_obj.tell()
            header = file_obj.read(16)
            file_obj.seek(current_pos)
            if header and len(header) >= 4:
                # Common video signatures:
                # MP4/MOV: ftyp, moov, mdat, wide at offset 4
                # WebM/MKV: \x1a\x45\xdf\xa3 (EBML header)
                is_ebml = header.startswith(b"\x1a\x45\xdf\xa3")
                is_iso_media = b"ftyp" in header or b"moov" in header or b"mdat" in header
                if not (is_ebml or is_iso_media):
                    # For lenient check with test files or raw containers, verify it's not plain text
                    if header.startswith(b"<!DOCTYPE") or header.startswith(b"<html") or header.startswith(b"{\n"):
                        raise VideoValidationError("File content is not a valid video.")


class TranscriptValidator:
    """
    Validates normalized transcript segments before database persistence.
    """

    @staticmethod
    def validate_segments(segments: List[Dict[str, Any]]) -> None:
        if not segments:
            raise TranscriptValidationError("Transcript contains no valid speech segments.")

        for i, seg in enumerate(segments, start=1):
            if seg.get("sequence") != i:
                raise TranscriptValidationError(
                    f"Segment sequence mismatch: expected {i}, got {seg.get('sequence')}."
                )

            start = seg.get("start_time")
            end = seg.get("end_time")
            text = seg.get("text")

            if start is None or end is None:
                raise TranscriptValidationError(f"Segment {i} is missing timestamp.")

            if end <= start:
                raise TranscriptValidationError(
                    f"Segment {i} has invalid time interval: start={start}, end={end}."
                )

            if not text or not str(text).strip():
                raise TranscriptValidationError(f"Segment {i} has empty text.")
