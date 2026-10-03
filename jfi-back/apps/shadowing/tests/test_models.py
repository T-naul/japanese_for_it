import uuid
from django.db import IntegrityError
from django.test import TestCase, override_settings
from apps.shadowing.models import ShadowingSegment, ShadowingVideo, VideoStatus
from .fixtures import create_mock_video_file


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ShadowingModelTests(TestCase):
    def setUp(self):
        self.video_file = create_mock_video_file("test_model.mp4")
        self.video = ShadowingVideo.objects.create(
            title="Business IT Greeting",
            description="Shadowing course for IT engineers",
            level="N3",
            language="ja",
            video_file=self.video_file,
            metadata={"source": "YouTube"},
        )

    def test_video_creation_and_defaults(self):
        self.assertIsInstance(self.video.id, uuid.UUID)
        self.assertEqual(self.video.status, VideoStatus.UPLOAD)
        self.assertEqual(self.video.language, "ja")
        self.assertEqual(self.video.level, "N3")
        self.assertEqual(self.video.error_message, "")
        self.assertEqual(self.video.metadata, {"source": "YouTube"})
        self.assertIsNone(self.video.duration_seconds)
        self.assertIsNone(self.video.file_size)
        self.assertIn("Business IT Greeting", str(self.video))

    def test_video_status_choices(self):
        for st in [VideoStatus.UPLOAD, VideoStatus.PROCESSING, VideoStatus.READY, VideoStatus.FAILED]:
            self.video.status = st
            self.video.save(update_fields=["status"])
            self.video.refresh_from_db()
            self.assertEqual(self.video.status, st)

    def test_segment_creation_and_defaults(self):
        seg = ShadowingSegment.objects.create(
            video=self.video,
            sequence=1,
            start_time=0.0,
            end_time=2.5,
            text="おはようございます。",
        )
        self.assertIsInstance(seg.id, uuid.UUID)
        self.assertEqual(seg.reading, "")
        self.assertEqual(seg.speaker, "")
        self.assertEqual(seg.metadata, {})
        self.assertIn("Seq 1", str(seg))

    def test_segment_sequence_uniqueness(self):
        ShadowingSegment.objects.create(
            video=self.video,
            sequence=1,
            start_time=0.0,
            end_time=1.5,
            text="First sentence.",
        )
        # Creating duplicate sequence for the same video should violate unique constraint
        with self.assertRaises(IntegrityError):
            ShadowingSegment.objects.create(
                video=self.video,
                sequence=1,
                start_time=1.5,
                end_time=3.0,
                text="Conflicting sequence.",
            )

    def test_segment_different_videos_same_sequence(self):
        video2 = ShadowingVideo.objects.create(
            title="Second Video",
            video_file=create_mock_video_file("v2.mp4"),
        )
        s1 = ShadowingSegment.objects.create(
            video=self.video,
            sequence=1,
            start_time=0.0,
            end_time=1.0,
            text="Text 1",
        )
        s2 = ShadowingSegment.objects.create(
            video=video2,
            sequence=1,
            start_time=0.0,
            end_time=1.0,
            text="Text 2",
        )
        self.assertNotEqual(s1.id, s2.id)

    def test_segment_ordering_by_sequence(self):
        ShadowingSegment.objects.create(video=self.video, sequence=2, start_time=2.0, end_time=4.0, text="B")
        ShadowingSegment.objects.create(video=self.video, sequence=1, start_time=0.0, end_time=2.0, text="A")
        ShadowingSegment.objects.create(video=self.video, sequence=3, start_time=4.0, end_time=6.0, text="C")

        seqs = list(self.video.segments.values_list("sequence", flat=True))
        self.assertEqual(seqs, [1, 2, 3])

    def test_segment_end_time_gte_start_time_constraint(self):
        # Database check constraint should reject end_time < start_time
        with self.assertRaises(IntegrityError):
            ShadowingSegment.objects.create(
                video=self.video,
                sequence=1,
                start_time=5.0,
                end_time=2.0,
                text="Invalid timing.",
            )
