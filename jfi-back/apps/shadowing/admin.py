from django.contrib import admin
from .models import ShadowingSegment, ShadowingVideo


@admin.register(ShadowingVideo)
class ShadowingVideoAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "status",
        "level",
        "language",
        "duration_seconds",
        "created_at",
        "error_message",
    ]
    list_filter = ["status", "level", "language", "created_at"]
    search_fields = ["title", "description", "error_message"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ShadowingSegment)
class ShadowingSegmentAdmin(admin.ModelAdmin):
    list_display = [
        "video",
        "sequence",
        "start_time",
        "end_time",
        "text",
        "reading",
    ]
    list_filter = ["video"]
    search_fields = ["text", "reading", "speaker"]
    readonly_fields = ["id", "created_at", "updated_at"]
