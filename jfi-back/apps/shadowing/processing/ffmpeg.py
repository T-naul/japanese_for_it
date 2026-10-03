import json
import logging
import os
import subprocess
from typing import Any, Dict, Optional, Tuple

from .exceptions import AudioExtractionError

logger = logging.getLogger(__name__)


class FFmpegAudioExtractor:
    """
    Handles audio extraction and media probing using FFmpeg / FFprobe.
    Ensures safe subprocess execution without shell=True, internal error capture,
    and no leaking of raw system output to client layers.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def extract_audio(
        self,
        input_video_path: str,
        output_wav_path: str,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> str:
        """
        Extracts audio from video to a 16kHz mono WAV file.
        """
        if not os.path.exists(input_video_path):
            raise AudioExtractionError("Input video file does not exist.")

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i",
            input_video_path,
            "-vn",
            "-ac",
            str(channels),
            "-ar",
            str(sample_rate),
            output_wav_path,
        ]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            if process.returncode != 0:
                logger.error(
                    "FFmpeg audio extraction failed with code %d. Stderr: %s",
                    process.returncode,
                    process.stderr,
                )
                raise AudioExtractionError("Audio extraction failed.")

            if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
                logger.error("FFmpeg generated empty or missing output audio.")
                raise AudioExtractionError("Audio extraction failed.")

            return output_wav_path
        except FileNotFoundError:
            logger.error("FFmpeg binary not found at path: %s", self.ffmpeg_path)
            raise AudioExtractionError("Audio extraction tool unavailable.")
        except AudioExtractionError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during audio extraction: %s", str(e))
            raise AudioExtractionError("Audio extraction failed.")

    def probe_video(self, video_path: str) -> Dict[str, Any]:
        """
        Extracts media metadata (duration_seconds, width, height, fps, codecs).
        Returns a dictionary. Failures in optional metadata extraction do not break processing.
        """
        metadata: Dict[str, Any] = {}
        if not os.path.exists(video_path):
            return metadata

        cmd = [
            self.ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            if process.returncode == 0 and process.stdout:
                info = json.loads(process.stdout)
                format_info = info.get("format", {})
                if "duration" in format_info:
                    try:
                        metadata["duration_seconds"] = float(format_info["duration"])
                    except (ValueError, TypeError):
                        pass

                if "size" in format_info:
                    try:
                        metadata["file_size"] = int(format_info["size"])
                    except (ValueError, TypeError):
                        pass

                streams = info.get("streams", [])
                for stream in streams:
                    codec_type = stream.get("codec_type")
                    if codec_type == "video" and "width" not in metadata:
                        metadata["width"] = stream.get("width")
                        metadata["height"] = stream.get("height")
                        metadata["video_codec"] = stream.get("codec_name")
                        r_frame_rate = stream.get("r_frame_rate", "")
                        if "/" in r_frame_rate:
                            try:
                                num, den = r_frame_rate.split("/")
                                if float(den) > 0:
                                    metadata["fps"] = round(float(num) / float(den), 2)
                            except Exception:
                                pass
                    elif codec_type == "audio" and "audio_codec" not in metadata:
                        metadata["audio_codec"] = stream.get("codec_name")
                        metadata["sample_rate"] = stream.get("sample_rate")
        except Exception as e:
            logger.warning("FFprobe metadata extraction failed or unavailable: %s", str(e))

        return metadata
