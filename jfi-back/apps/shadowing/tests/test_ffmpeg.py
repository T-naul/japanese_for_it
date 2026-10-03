import json
import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch
from django.test import TestCase

from apps.shadowing.processing.exceptions import AudioExtractionError
from apps.shadowing.processing.ffmpeg import FFmpegAudioExtractor


class FFmpegTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.extractor = FFmpegAudioExtractor()

        # Create dummy input video file
        self.input_video = os.path.join(self.temp_dir.name, "input.mp4")
        with open(self.input_video, "wb") as f:
            f.write(b"dummy video data")

        self.output_wav = os.path.join(self.temp_dir.name, "output.wav")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("subprocess.run")
    def test_command_construction_and_no_shell(self, mock_run):
        # Create output file so post-check passes
        def fake_run(cmd, **kwargs):
            self.assertFalse(kwargs.get("shell", False))
            self.assertIsInstance(cmd, list)
            self.assertEqual(cmd[0], "ffmpeg")
            self.assertIn("-vn", cmd)
            self.assertIn("-ac", cmd)
            self.assertIn("-ar", cmd)
            with open(self.output_wav, "wb") as f:
                f.write(b"RIFF dummy wav data")
            return MagicMock(returncode=0, stderr="")

        mock_run.side_effect = fake_run

        result_path = self.extractor.extract_audio(self.input_video, self.output_wav)
        self.assertEqual(result_path, self.output_wav)
        mock_run.assert_called_once()

    def test_missing_input_file_raises_error(self):
        non_existent = os.path.join(self.temp_dir.name, "ghost.mp4")
        with self.assertRaises(AudioExtractionError) as ctx:
            self.extractor.extract_audio(non_existent, self.output_wav)
        self.assertIn("does not exist", str(ctx.exception).lower())

    @patch("subprocess.run")
    def test_ffmpeg_nonzero_exit_raises_safe_error(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Internal ffmpeg crash traceback and path /var/private/secret",
        )
        with self.assertRaises(AudioExtractionError) as ctx:
            self.extractor.extract_audio(self.input_video, self.output_wav)
        # Raw stderr must NOT be leaked
        self.assertEqual(str(ctx.exception), "Audio extraction failed.")
        self.assertNotIn("/var/private/secret", str(ctx.exception))

    @patch("subprocess.run")
    def test_ffmpeg_binary_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")
        with self.assertRaises(AudioExtractionError) as ctx:
            self.extractor.extract_audio(self.input_video, self.output_wav)
        self.assertIn("unavailable", str(ctx.exception).lower())

    @patch("subprocess.run")
    def test_ffmpeg_empty_output_file_raises_error(self, mock_run):
        def fake_run(cmd, **kwargs):
            # Output file created but 0 bytes
            with open(self.output_wav, "wb") as f:
                pass
            return MagicMock(returncode=0)

        mock_run.side_effect = fake_run
        with self.assertRaises(AudioExtractionError):
            self.extractor.extract_audio(self.input_video, self.output_wav)

    @patch("subprocess.run")
    def test_probe_video_successful(self, mock_run):
        ffprobe_data = {
            "format": {
                "duration": "45.67",
                "size": "1048576",
            },
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "codec_name": "h264",
                    "r_frame_rate": "30/1",
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                },
            ],
        }
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(ffprobe_data),
        )

        metadata = self.extractor.probe_video(self.input_video)
        self.assertEqual(metadata["duration_seconds"], 45.67)
        self.assertEqual(metadata["file_size"], 1048576)
        self.assertEqual(metadata["width"], 1920)
        self.assertEqual(metadata["height"], 1080)
        self.assertEqual(metadata["video_codec"], "h264")
        self.assertEqual(metadata["fps"], 30.0)
        self.assertEqual(metadata["audio_codec"], "aac")

    @patch("subprocess.run")
    def test_probe_video_failure_returns_empty_dict(self, mock_run):
        mock_run.side_effect = Exception("ffprobe error")
        metadata = self.extractor.probe_video(self.input_video)
        self.assertEqual(metadata, {})
