from django.test import TestCase, override_settings

from apps.shadowing.models import ShadowingSegment, ShadowingVideo
from apps.shadowing.processing.persistence import ShadowingPersistenceService
from .fixtures import create_mock_video_file


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PersistenceTests(TestCase):
    def setUp(self):
        self.video = ShadowingVideo.objects.create(
            title="Persist Test Video",
            video_file=create_mock_video_file("persist.mp4"),
        )

    def test_persist_segments_bulk_create(self):
        data = [
            {"sequence": 1, "start_time": 0.0, "end_time": 1.5, "text": "First", "reading": "1", "speaker": "A", "metadata": {"note": "x"}},
            {"sequence": 2, "start_time": 1.5, "end_time": 3.0, "text": "Second", "reading": "2", "speaker": "B", "metadata": {"note": "y"}},
        ]
        segments = ShadowingPersistenceService.persist_segments(self.video, data)
        self.assertEqual(len(segments), 2)
        self.assertEqual(ShadowingSegment.objects.filter(video=self.video).count(), 2)

        s1 = ShadowingSegment.objects.get(video=self.video, sequence=1)
        self.assertEqual(s1.text, "First")
        self.assertEqual(s1.reading, "1")
        self.assertEqual(s1.speaker, "A")
        self.assertEqual(s1.metadata, {"note": "x"})

    def test_persist_segments_replaces_stale_records(self):
        # Initial persistence
        initial_data = [
            {"sequence": 1, "start_time": 0.0, "end_time": 1.0, "text": "Old 1"},
            {"sequence": 2, "start_time": 1.0, "end_time": 2.0, "text": "Old 2"},
            {"sequence": 3, "start_time": 2.0, "end_time": 3.0, "text": "Old 3"},
        ]
        ShadowingPersistenceService.persist_segments(self.video, initial_data)
        self.assertEqual(self.video.segments.count(), 3)

        # Reprocessing with new data (only 1 segment)
        new_data = [
            {"sequence": 1, "start_time": 0.0, "end_time": 5.0, "text": "New combined segment"},
        ]
        ShadowingPersistenceService.persist_segments(self.video, new_data)
        self.assertEqual(self.video.segments.count(), 1)
        self.assertEqual(self.video.segments.first().text, "New combined segment")
