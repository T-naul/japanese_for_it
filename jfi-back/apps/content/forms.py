from django import forms


class ContentImportForm(forms.Form):
    CONTENT_TYPES = [
        ("vocabulary", "Vocabulary"),
        ("grammar", "Grammar"),
    ]

    content_type = forms.ChoiceField(
        choices=CONTENT_TYPES,
        label="Content type",
    )

    file = forms.FileField(
        label="File",
        help_text="Supported formats: CSV, XLSX, JSON",
    )