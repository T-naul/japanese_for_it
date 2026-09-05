from django.contrib import admin

from .models import (
    Vocabulary,
    VocabularyForm,
    Grammar,
    Source,
)


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = (
        "kanji",
        "hiragana",
        "meaning",
        "word_type",
        "level",
        "status",
        "version",
    )

    list_filter = (
        "level",
        "word_type",
        "status",
    )

    search_fields = (
        "kanji",
        "hiragana",
        "meaning",
    )


@admin.register(VocabularyForm)
class VocabularyFormAdmin(admin.ModelAdmin):
    list_display = (
        "vocabulary",
        "form_type",
        "value",
    )

    list_filter = ("form_type",)


@admin.register(Grammar)
class GrammarAdmin(admin.ModelAdmin):
    list_display = (
        "pattern",
        "meaning",
        "level",
        "status",
        "version",
    )

    list_filter = (
        "level",
        "status",
    )

    search_fields = (
        "pattern",
        "meaning",
    )


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
    )

    search_fields = ("name",)