from django.contrib import admin

from .models import (
    Vocabulary,
    VocabularyForm,
    Grammar,
    Source,
)

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from .forms import ContentImportForm
from .services import (
    import_grammars,
    import_vocabularies,
    read_import_file,
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
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(
                    content_import_view
                ),
                name="content_import",
            ),
        ]

        return custom_urls + urls


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

def content_import_view(request):
    result = None

    if request.method == "POST":
        form = ContentImportForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            content_type = form.cleaned_data[
                "content_type"
            ]

            uploaded_file = form.cleaned_data[
                "file"
            ]

            try:
                rows = read_import_file(
                    uploaded_file
                )

                if not rows:
                    form.add_error(
                        "file",
                        "File không có dữ liệu.",
                    )
                elif content_type == "vocabulary":
                    result = import_vocabularies(
                        rows
                    )
                else:
                    result = import_grammars(
                        rows
                    )

            except Exception as exc:
                form.add_error(
                    "file",
                    str(exc),
                )

    else:
        form = ContentImportForm()

    context = {
        **admin.site.each_context(request),
        "title": "Import Center",
        "form": form,
        "result": result,
    }

    return TemplateResponse(
        request,
        "admin/content/import.html",
        context,
    )
