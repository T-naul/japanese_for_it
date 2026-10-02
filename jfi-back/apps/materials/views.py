from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import LearningMaterial, MaterialStatus, UserMaterial
from .pagination import StandardResultsSetPagination
from .serializers import (
    LessonCompletionResponseSerializer,
    MaterialCreateResponseSerializer,
    MaterialCreateSerializer,
    MaterialDetailSerializer,
    MaterialLessonDetailSerializer,
    MaterialLessonListSerializer,
    MaterialListSerializer,
    MaterialSectionSerializer,
    MaterialUpdateSerializer,
    ProcessingStatusSerializer,
    UserMaterialDetailSerializer,
    UserMaterialListSerializer,
)
from .services import (
    EnrollmentService,
    LessonService,
    MaterialService,
    ProcessingService,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Materials"],
        summary="List Learning Materials",
        description="Admins see all materials; normal users see only ready materials.",
    ),
    retrieve=extend_schema(
        tags=["Materials"],
        summary="Retrieve Learning Material Detail",
        description="Get material details. Only ready materials are visible to non-admin users.",
    ),
    create=extend_schema(
        tags=["Materials"],
        summary="Create Learning Material with PDF",
        description="Upload a PDF and metadata to create a new LearningMaterial and queue background processing.",
        request=MaterialCreateSerializer,
        responses={201: MaterialCreateResponseSerializer},
    ),
    partial_update=extend_schema(
        tags=["Materials"],
        summary="Update Learning Material Metadata or File",
        description="Admin-only update of safe metadata or replacement of PDF file.",
        request=MaterialUpdateSerializer,
        responses={200: MaterialDetailSerializer},
    ),
    destroy=extend_schema(
        tags=["Materials"],
        summary="Delete Learning Material",
        description="Admin-only delete. Cannot delete while processing.",
        responses={204: None, 409: None},
    ),
)
class LearningMaterialViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "status",
        "material_type",
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
        return MaterialService.get_materials_queryset(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return MaterialListSerializer
        if self.action == "create":
            return MaterialCreateSerializer
        if self.action in ["update", "partial_update"]:
            return MaterialUpdateSerializer
        return MaterialDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = request.FILES.get("file")
        material, job = MaterialService.create_material(
            user=request.user,
            data=serializer.validated_data,
            file_obj=file_obj,
        )

        job_status_data = ProcessingService.get_material_processing_status(material)
        response_data = {
            "material": MaterialDetailSerializer(material, context={"request": request}).data,
            "job": job_status_data,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        material = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        file_obj = request.FILES.get("file")
        updated_material, new_job = MaterialService.update_material(
            material=material,
            user=request.user,
            data=serializer.validated_data,
            file_obj=file_obj,
        )

        data = MaterialDetailSerializer(updated_material, context={"request": request}).data
        if new_job:
            data["job"] = ProcessingService.get_material_processing_status(updated_material)
        return Response(data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        material = self.get_object()
        MaterialService.delete_material(material)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Materials"],
        summary="Get Material Processing Status",
        description="Admin-only inspection of the current/latest processing job.",
        responses={200: ProcessingStatusSerializer, 404: None},
    )
    @action(detail=True, methods=["get"], url_path="processing")
    def processing_status(self, request, pk=None):
        material = self.get_object()
        job_status = ProcessingService.get_material_processing_status(material)
        if not job_status:
            return Response(
                {"error": "No processing job found for this material."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(job_status, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Materials"],
        summary="Enroll into Material",
        description="Enroll the authenticated user into a ready material.",
        responses={200: None, 201: None, 400: None},
    )
    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        material = self.get_object()
        user_material, created = EnrollmentService.enroll_user(request.user, material)
        res_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "enrolled": True,
                "material_id": str(material.id),
                "status": user_material.status,
            },
            status=res_status,
        )

    @extend_schema(
        tags=["Materials"],
        summary="List Material Lessons",
        description="Get lessons of this material ordered by lesson_number.",
        responses={200: MaterialLessonListSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="lessons")
    def lessons(self, request, pk=None):
        material = self.get_object()
        lessons_qs = LessonService.get_lessons_for_material(material, user=request.user)
        serializer = MaterialLessonListSerializer(lessons_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Materials"],
        summary="Retrieve Material Lesson Detail",
        description="Get specific lesson details.",
        responses={200: MaterialLessonDetailSerializer, 404: None},
    )
    @action(
        detail=True,
        methods=["get"],
        url_path=r"lessons/(?P<lesson_id>[^/.]+)",
    )
    def lesson_detail(self, request, pk=None, lesson_id=None):
        material = self.get_object()
        lesson = LessonService.get_lesson_detail(material, lesson_id, user=request.user)
        serializer = MaterialLessonDetailSerializer(lesson)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Materials"],
        summary="List Lesson Sections",
        description="Get sections of a lesson ordered by order.",
        responses={200: MaterialSectionSerializer(many=True), 404: None},
    )
    @action(
        detail=True,
        methods=["get"],
        url_path=r"lessons/(?P<lesson_id>[^/.]+)/sections",
    )
    def lesson_sections(self, request, pk=None, lesson_id=None):
        material = self.get_object()
        sections_qs = LessonService.get_sections_for_lesson(material, lesson_id)
        serializer = MaterialSectionSerializer(sections_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["My Materials"],
        summary="List Enrolled Materials",
        description="List all materials the authenticated user is currently enrolled in.",
        responses={200: UserMaterialListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["My Materials"],
        summary="Retrieve Enrolled Material Detail",
        description="Get enrolled material detail with progress and lesson completion states.",
        responses={200: UserMaterialDetailSerializer, 404: None},
    ),
)
class MyMaterialViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return UserMaterial.objects.none()
        return (
            UserMaterial.objects.filter(user=self.request.user)
            .select_related("material")
            .prefetch_related("lessons__lesson", "material__lessons")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return UserMaterialListSerializer
        return UserMaterialDetailSerializer

    def get_object(self):
        lookup_val = self.kwargs[self.lookup_field]
        # Allow looking up by material_id as primary, or UserMaterial id
        user_material = (
            UserMaterial.objects.filter(user=self.request.user, material_id=lookup_val)
            .select_related("material")
            .prefetch_related("lessons__lesson", "material__lessons")
            .first()
        )
        if not user_material:
            user_material = (
                UserMaterial.objects.filter(user=self.request.user, id=lookup_val)
                .select_related("material")
                .prefetch_related("lessons__lesson", "material__lessons")
                .first()
            )
        if not user_material:
            raise Http404("Enrolled material not found.")
        return user_material

    @extend_schema(
        tags=["My Materials"],
        summary="Complete a Lesson",
        description="Mark a lesson completed and recalculate material progress.",
        responses={200: LessonCompletionResponseSerializer, 400: None, 404: None},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"lessons/(?P<lesson_id>[^/.]+)/complete",
    )
    def complete_lesson(self, request, pk=None, lesson_id=None):
        user_material = self.get_object()
        result = LessonService.complete_lesson(
            user=request.user,
            material_id=user_material.material_id,
            lesson_id=lesson_id,
        )
        return Response(result, status=status.HTTP_200_OK)
