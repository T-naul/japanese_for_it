from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.shadowing.processing.exceptions import VideoValidationError
from apps.shadowing.processing.validator import VideoValidator
from apps.shadowing.services import ShadowingVideoService
from .fixtures import MOCK_MP4_BYTES, MOCK_WEBM_BYTES, create_mock_video_file

User = get_user_model()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    MAX_SHADOWING_VIDEO_SIZE_MB=10,
)
class VideoValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="validator_user", password="password123")

    def test_missing_file_raises_error(self):
        with self.assertRaises(VideoValidationError) as ctx:
            VideoValidator.validate_uploaded_file(None)
        self.assertIn("required", str(ctx.exception).lower())

    def test_empty_filename_raises_error(self):
        from unittest.mock import MagicMock
        fake_file = MagicMock()
        fake_file.name = ""
        with self.assertRaises(VideoValidationError) as ctx:
            VideoValidator.validate_uploaded_file(fake_file)
        self.assertIn("filename", str(ctx.exception).lower())

    def test_unsupported_extension_rejected(self):
        for bad_name in ["sample.pdf", "audio.mp3", "doc.docx", "virus.exe"]:
            f = SimpleUploadedFile(bad_name, b"data", content_type="application/octet-stream")
            with self.assertRaises(VideoValidationError) as ctx:
                VideoValidator.validate_uploaded_file(f)
            self.assertIn("unsupported", str(ctx.exception).lower())

    def test_empty_file_rejected(self):
        f = SimpleUploadedFile("empty.mp4", b"", content_type="video/mp4")
        with self.assertRaises(VideoValidationError) as ctx:
            VideoValidator.validate_uploaded_file(f)
        self.assertIn("empty", str(ctx.exception).lower())

    def test_oversized_file_rejected(self):
        # 11MB file with MAX_SHADOWING_VIDEO_SIZE_MB=10
        big_content = b"\x00\x00\x00\x18ftypmp42" + (b"\x00" * (11 * 1024 * 1024))
        f = SimpleUploadedFile("big.mp4", big_content, content_type="video/mp4")
        with self.assertRaises(VideoValidationError) as ctx:
            VideoValidator.validate_uploaded_file(f)
        self.assertIn("exceeds maximum", str(ctx.exception).lower())

    def test_disguised_html_rejected(self):
        html_content = b"<!DOCTYPE html><html><body>Fake video</body></html>"
        f = SimpleUploadedFile("fake.mp4", html_content, content_type="video/mp4")
        with self.assertRaises(VideoValidationError) as ctx:
            VideoValidator.validate_uploaded_file(f)
        self.assertIn("not a valid video", str(ctx.exception).lower())

    def test_supported_extensions_accepted(self):
        for name, data in [
            ("valid.mp4", MOCK_MP4_BYTES),
            ("valid.webm", MOCK_WEBM_BYTES),
            ("valid.mov", MOCK_MP4_BYTES),
            ("valid.mkv", MOCK_WEBM_BYTES),
        ]:
            f = SimpleUploadedFile(name, data, content_type="video/mp4")
            # Should not raise exception
            VideoValidator.validate_uploaded_file(f)

    def test_service_create_video_missing_title(self):
        f = create_mock_video_file("test.mp4")
        with self.assertRaises(VideoValidationError) as ctx:
            ShadowingVideoService.create_video(
                user=self.user,
                data={"title": ""},
                file_obj=f,
            )
        self.assertIn("title is required", str(ctx.exception).lower())
