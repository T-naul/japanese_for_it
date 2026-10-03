import abc
import logging
from typing import Any, Dict, List

from .exceptions import TranscriptionError

logger = logging.getLogger(__name__)


class TranscriptionService(abc.ABC):
    """
    Abstract interface for speech-to-text audio transcription.
    Allows swappable backends (e.g. Whisper, faster-whisper, mock/stub).
    """

    @abc.abstractmethod
    def transcribe(self, audio_path: str, language: str = "ja") -> List[Dict[str, Any]]:
        """
        Transcribes the audio file at audio_path.
        Returns a list of segment dictionaries with:
        - start_time: float
        - end_time: float
        - text: str
        - reading: str (optional, default "")
        - speaker: str (optional, default "")
        - metadata: dict (optional)
        """
        pass


class MockTranscriptionService(TranscriptionService):
    """
    Deterministic mock transcription service for testing without requiring
    GPU, external APIs, or downloading heavy AI weights.
    """

    def __init__(self, predefined_segments: List[Dict[str, Any]] = None):
        self.predefined_segments = predefined_segments

    def transcribe(self, audio_path: str, language: str = "ja") -> List[Dict[str, Any]]:
        if self.predefined_segments is not None:
            return self.predefined_segments

        # Default synthetic transcription segments
        return [
            {
                "start_time": 0.0,
                "end_time": 2.5,
                "text": "こんにちは、初めまして。",
                "reading": "",
                "speaker": "Speaker 1",
                "metadata": {"confidence": 0.95},
            },
            {
                "start_time": 2.8,
                "end_time": 5.2,
                "text": "本日のIT日本語のレッスンを始めましょう。",
                "reading": "",
                "speaker": "Speaker 1",
                "metadata": {"confidence": 0.92},
            },
        ]
