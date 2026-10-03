import logging
from typing import Any, Dict, List
from django.db import transaction

from apps.shadowing.models import ShadowingSegment, ShadowingVideo

logger = logging.getLogger(__name__)


class ShadowingPersistenceService:
    """
    Handles atomic, short-lived transactional persistence of normalized shadowing segments.
    Ensures safe idempotent re-runs by wiping stale segments before bulk-inserting new ones.
    """

    @staticmethod
    def persist_segments(
        video: ShadowingVideo,
        segments_data: List[Dict[str, Any]],
    ) -> List[ShadowingSegment]:
        """
        Atomically replaces stale segments with newly normalized segments.
        Held strictly during the DB write, not during audio extraction or transcription.
        """
        segment_objs = [
            ShadowingSegment(
                video=video,
                sequence=item["sequence"],
                start_time=item["start_time"],
                end_time=item["end_time"],
                text=item["text"],
                reading=item.get("reading", ""),
                speaker=item.get("speaker", ""),
                metadata=item.get("metadata", {}),
            )
            for item in segments_data
        ]

        with transaction.atomic():
            # Delete stale segments if this video was previously processed/reprocessed
            ShadowingSegment.objects.filter(video=video).delete()
            created_segments = ShadowingSegment.objects.bulk_create(segment_objs)

        logger.info(
            "Persisted %d shadowing segments for video_id=%s",
            len(created_segments),
            video.id,
        )
        return created_segments
