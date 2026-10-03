from django.core.files.uploadedfile import SimpleUploadedFile

# Valid mock MP4 header (ftyp box)
MOCK_MP4_BYTES = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 64
MOCK_WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 64


def create_mock_video_file(name: str = "sample.mp4", content: bytes = None) -> SimpleUploadedFile:
    if content is None:
        content = MOCK_MP4_BYTES
    return SimpleUploadedFile(name, content, content_type="video/mp4")
