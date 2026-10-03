from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import ShadowingVideo, UserShadowingVideo
from .pagination import StandardResultsSetPagination
from .serializers import (
    EnrollmentResponseSerializer,
    SegmentCompletionResponseSerializer,
    ShadowingProcessingStatusSerializer,
    ShadowingSegmentSerializer,
    ShadowingVideoCreateResponseSerializer,
    ShadowingVideoCreateSerializer,
    ShadowingVideoDetailSerializer,
    ShadowingVideoListSerializer,
    ShadowingVideoUpdateSerializer,
    UserShadowingDetailSerializer,
    UserShadowingListSerializer,
)
from .services import (
    ShadowingEnrollmentService,
    ShadowingProcessingService,
    ShadowingProgressService,
    ShadowingSegmentService,
    ShadowingVideoService,
)
from .processing.exceptions import VideoValidationError


@extend_schema_view(
    list=extend_schema(
        tags=["Shadowing"],
        summary="List Shadowing Videos",
        description="Admins see all videos; normal users see only ready videos.",
        responses={200: ShadowingVideoListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Shadowing"],
        summary="Retrieve Shadowing Video Detail",
        description="Admins can inspect all states; normal users can inspect ready only.",
        responses={200: ShadowingVideoDetailSerializer, 404: None},
    ),
    create=extend_schema(
        tags=["Shadowing"],
        summary="Upload Video for Shadowing",
        description="Upload a video file and metadata to create a ShadowingVideo and queue background processing.",
        request=ShadowingVideoCreateSerializer,
        responses={201: ShadowingVideoCreateResponseSerializer, 400: None},
    ),
    partial_update=extend_schema(
        tags=["Shadowing"],
        summary="Update Shadowing Video Metadata or File",
        description="Admin-only update of safe metadata or replacement of video file.",
        request=ShadowingVideoUpdateSerializer,
        responses={200: ShadowingVideoDetailSerializer, 400: None, 409: None},
    ),
    destroy=extend_schema(
        tags=["Shadowing"],
        summary="Delete Shadowing Video",
        description="Admin-only delete. Cannot delete while processing.",
        responses={204: None, 409: None},
    ),
)
class ShadowingVideoViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "status",
        "level",
        "language",
    ]
    search_fields = [
        "title",
        "description",
    ]
    ordering_fields = [
        "created_at",
        "title",
        "level",
    ]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "processing_status"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ShadowingVideo.objects.none()
        return ShadowingVideoService.get_videos_queryset(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ShadowingVideoListSerializer
        if self.action == "create":
            return ShadowingVideoCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ShadowingVideoUpdateSerializer
        return ShadowingVideoDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = request.FILES.get("video_file")
        try:
            video, job = ShadowingVideoService.create_video(
                user=request.user,
                data=serializer.validated_data,
                file_obj=file_obj,
            )
        except VideoValidationError as e:
            raise exceptions.ValidationError({"video_file": str(e)})

        job_status_data = ShadowingProcessingService.get_video_processing_status(video)
        response_data = {
            "video": ShadowingVideoDetailSerializer(video, context={"request": request}).data,
            "job": job_status_data,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        video = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        file_obj = request.FILES.get("video_file")
        try:
            updated_video, new_job = ShadowingVideoService.update_video(
                video=video,
                user=request.user,
                data=serializer.validated_data,
                file_obj=file_obj,
            )
        except VideoValidationError as e:
            raise exceptions.ValidationError({"video_file": str(e)})

        data = ShadowingVideoDetailSerializer(updated_video, context={"request": request}).data
        if new_job:
            data["job"] = ShadowingProcessingService.get_video_processing_status(updated_video)
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        video = self.get_object()
        ShadowingVideoService.delete_video(video)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Shadowing"],
        summary="Get Video Processing Status",
        description="Admin-only inspection of the current/latest processing job.",
        responses={200: ShadowingProcessingStatusSerializer, 404: None},
    )
    @action(detail=True, methods=["get"], url_path="processing")
    def processing_status(self, request, pk=None):
        video = self.get_object()
        job_status = ShadowingProcessingService.get_video_processing_status(video)
        if not job_status:
            return Response(
                {"error": "No processing job found for this video."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(job_status, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Shadowing"],
        summary="List Video Segments",
        description="Get ordered segments for this video by sequence ASC.",
        responses={200: ShadowingSegmentSerializer(many=True), 404: None},
    )
    @action(detail=True, methods=["get"], url_path="segments")
    def segments(self, request, pk=None):
        video = self.get_object()
        segments_qs = ShadowingSegmentService.get_segments_for_video(video, user=request.user)
        serializer = ShadowingSegmentSerializer(segments_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Shadowing"],
        summary="Enroll into Shadowing Video",
        description="Enroll the authenticated user into a ready video. Idempotent.",
        responses={200: EnrollmentResponseSerializer, 201: EnrollmentResponseSerializer, 400: None, 404: None},
    )
    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        video = self.get_object()
        user_video, created = ShadowingEnrollmentService.enroll_user(request.user, video)
        res_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "enrolled": True,
                "video_id": str(video.id),
                "status": user_video.status,
            },
            status=res_status,
        )


@extend_schema_view(
    list=extend_schema(
        tags=["My Shadowing"],
        summary="List Enrolled Shadowing Videos",
        description="List all videos the authenticated user is currently enrolled in.",
        responses={200: UserShadowingListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["My Shadowing"],
        summary="Retrieve Enrolled Shadowing Video Detail",
        description="Get enrolled video detail with progress and segment completion states.",
        responses={200: UserShadowingDetailSerializer, 404: None},
    ),
)
class MyShadowingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return UserShadowingVideo.objects.none()
        return (
            UserShadowingVideo.objects.filter(user=self.request.user)
            .select_related("video")
            .prefetch_related("segment_progress__segment", "video__segments")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return UserShadowingListSerializer
        return UserShadowingDetailSerializer

    def get_object(self):
        lookup_val = self.kwargs[self.lookup_field]
        # Allow looking up by video_id as primary, or UserShadowingVideo id
        user_video = (
            UserShadowingVideo.objects.filter(user=self.request.user, video_id=lookup_val)
            .select_related("video")
            .prefetch_related("segment_progress__segment", "video__segments")
            .first()
        )
        if not user_video:
            user_video = (
                UserShadowingVideo.objects.filter(user=self.request.user, id=lookup_val)
                .select_related("video")
                .prefetch_related("segment_progress__segment", "video__segments")
                .first()
            )
        if not user_video:
            raise Http404("Enrolled video not found.")
        return user_video

    @extend_schema(
        tags=["My Shadowing"],
        summary="Complete a Video Segment",
        description="Mark a segment completed and recalculate video progress.",
        parameters=[
            OpenApiParameter("segment_id", OpenApiTypes.UUID, OpenApiParameter.PATH, description="UUID of the segment"),
        ],
        responses={200: SegmentCompletionResponseSerializer, 400: None, 404: None},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"segments/(?P<segment_id>[^/.]+)/complete",
    )
    def complete_segment(self, request, pk=None, segment_id=None):
        user_video = self.get_object()
        result = ShadowingProgressService.complete_segment(
            user=request.user,
            video_id=user_video.video_id,
            segment_id=segment_id,
        )
        return Response(result, status=status.HTTP_200_OK)
