from django.test import TestCase

from apps.shadowing.processing.exceptions import TranscriptValidationError
from apps.shadowing.processing.normalizer import TranscriptNormalizer
from apps.shadowing.processing.transcription import MockTranscriptionService
from apps.shadowing.processing.validator import TranscriptValidator


class TranscriptionAndNormalizerTests(TestCase):
    def test_mock_transcription_default_segments(self):
        service = MockTranscriptionService()
        segments = service.transcribe("dummy_audio.wav", language="ja")
        self.assertIsInstance(segments, list)
        self.assertGreater(len(segments), 0)
        self.assertIn("start_time", segments[0])
        self.assertIn("text", segments[0])

    def test_mock_transcription_custom_segments(self):
        custom = [{"start_time": 0.0, "end_time": 1.0, "text": "Test"}]
        service = MockTranscriptionService(predefined_segments=custom)
        res = service.transcribe("dummy_audio.wav")
        self.assertEqual(res, custom)

    def test_normalizer_removes_empty_and_whitespace_text(self):
        raw = [
            {"start_time": 0.0, "end_time": 1.0, "text": "   "},
            {"start_time": 1.0, "end_time": 2.0, "text": ""},
            {"start_time": 2.0, "end_time": 3.0, "text": "  Valid text  "},
            {"start_time": 3.0, "end_time": 4.0, "text": None},
        ]
        normalized = TranscriptNormalizer.normalize(raw)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["text"], "Valid text")
        self.assertEqual(normalized[0]["sequence"], 1)

    def test_normalizer_removes_invalid_timestamps(self):
        raw = [
            # end <= start
            {"start_time": 2.0, "end_time": 1.0, "text": "Backwards"},
            # equal
            {"start_time": 2.0, "end_time": 2.0, "text": "Zero duration"},
            # non-numeric
            {"start_time": "invalid", "end_time": 3.0, "text": "Corrupt start"},
            # valid
            {"start_time": 0.5, "end_time": 1.5, "text": "Good segment"},
        ]
        normalized = TranscriptNormalizer.normalize(raw)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["text"], "Good segment")
        self.assertEqual(normalized[0]["start_time"], 0.5)
        self.assertEqual(normalized[0]["end_time"], 1.5)
        self.assertEqual(normalized[0]["sequence"], 1)

    def test_normalizer_assigns_consecutive_sequences(self):
        raw = [
            {"start_time": 0.0, "end_time": 1.0, "text": "First"},
            {"start_time": 1.0, "end_time": 2.0, "text": ""},  # dropped
            {"start_time": 2.0, "end_time": 3.0, "text": "Second"},
            {"start_time": 3.0, "end_time": 4.0, "text": "Third"},
        ]
        normalized = TranscriptNormalizer.normalize(raw)
        self.assertEqual(len(normalized), 3)
        self.assertEqual([s["sequence"] for s in normalized], [1, 2, 3])
        self.assertEqual([s["text"] for s in normalized], ["First", "Second", "Third"])

    def test_normalizer_preserves_metadata(self):
        raw = [
            {
                "start_time": 0.0,
                "end_time": 1.5,
                "text": "Hello",
                "reading": "ハロー",
                "speaker": "Alice",
                "metadata": {"confidence": 0.99},
            }
        ]
        normalized = TranscriptNormalizer.normalize(raw)
        self.assertEqual(normalized[0]["reading"], "ハロー")
        self.assertEqual(normalized[0]["speaker"], "Alice")
        self.assertEqual(normalized[0]["metadata"], {"confidence": 0.99})

    def test_validator_passes_valid_segments(self):
        segments = [
            {"sequence": 1, "start_time": 0.0, "end_time": 1.5, "text": "One"},
            {"sequence": 2, "start_time": 1.5, "end_time": 3.0, "text": "Two"},
        ]
        # Should not raise
        TranscriptValidator.validate_segments(segments)

    def test_validator_empty_segments_raises(self):
        with self.assertRaises(TranscriptValidationError) as ctx:
            TranscriptValidator.validate_segments([])
        self.assertIn("no valid speech segments", str(ctx.exception).lower())

    def test_validator_sequence_gap_raises(self):
        segments = [
            {"sequence": 1, "start_time": 0.0, "end_time": 1.0, "text": "A"},
            {"sequence": 3, "start_time": 1.0, "end_time": 2.0, "text": "B"},
        ]
        with self.assertRaises(TranscriptValidationError) as ctx:
            TranscriptValidator.validate_segments(segments)
        self.assertIn("sequence mismatch", str(ctx.exception).lower())

    def test_validator_invalid_time_interval_raises(self):
        segments = [
            {"sequence": 1, "start_time": 2.0, "end_time": 1.0, "text": "Bad time"},
        ]
        with self.assertRaises(TranscriptValidationError) as ctx:
            TranscriptValidator.validate_segments(segments)
        self.assertIn("invalid time interval", str(ctx.exception).lower())

    def test_validator_missing_text_raises(self):
        segments = [
            {"sequence": 1, "start_time": 0.0, "end_time": 1.0, "text": "   "},
        ]
        with self.assertRaises(TranscriptValidationError) as ctx:
            TranscriptValidator.validate_segments(segments)
        self.assertIn("empty text", str(ctx.exception).lower())
