import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TranscriptNormalizer:
    """
    Normalizes raw transcription segments:
    - Filters out empty or whitespace-only text
    - Strips whitespace
    - Ensures start_time and end_time are valid floats
    - Ensures end_time > start_time
    - Assigns deterministic 1-based sequential ordering
    - Preserves metadata
    """

    @staticmethod
    def normalize(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        sequence = 1

        for raw in segments:
            if not isinstance(raw, dict):
                continue

            text = raw.get("text", "")
            if not isinstance(text, str):
                text = str(text) if text is not None else ""

            text = text.strip()
            if not text:
                continue

            try:
                start_time = float(raw.get("start_time", 0.0))
                end_time = float(raw.get("end_time", 0.0))
            except (ValueError, TypeError):
                logger.warning("Skipping segment with invalid timestamp: %s", raw)
                continue

            # Must satisfy end_time > start_time
            if end_time <= start_time:
                logger.warning(
                    "Skipping segment where end_time (%.2f) <= start_time (%.2f)",
                    end_time,
                    start_time,
                )
                continue

            reading = str(raw.get("reading", "") or "").strip()
            speaker = str(raw.get("speaker", "") or "").strip()
            metadata = raw.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            normalized.append(
                {
                    "sequence": sequence,
                    "start_time": round(start_time, 3),
                    "end_time": round(end_time, 3),
                    "text": text,
                    "reading": reading,
                    "speaker": speaker,
                    "metadata": dict(metadata),
                }
            )
            sequence += 1

        return normalized
