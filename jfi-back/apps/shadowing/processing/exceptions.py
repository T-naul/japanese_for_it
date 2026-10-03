class ShadowingProcessingError(Exception):
    """Base exception for shadowing processing errors."""
    pass


class VideoValidationError(ShadowingProcessingError):
    """Raised when video file validation fails."""
    pass


class AudioExtractionError(ShadowingProcessingError):
    """Raised when audio extraction via FFmpeg fails."""
    pass


class TranscriptionError(ShadowingProcessingError):
    """Raised when audio transcription fails."""
    pass


class TranscriptValidationError(ShadowingProcessingError):
    """Raised when transcript validation or normalization fails."""
    pass
