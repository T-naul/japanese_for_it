# pyrefly: ignore [missing-import]
from django.db import transaction

from .models import (
    Grammar,
    Source,
    Vocabulary,
    VocabularyForm,
)


class VocabularyService:

    @staticmethod
    def _validate_forms(
        vocabulary,
        forms_data,
    ):
        """
        Business validation cho verb forms.
        """

        if not forms_data:
            return

        if vocabulary.word_type != "verb" and not str(vocabulary.word_type).startswith("verb"):
            raise ValueError(
                "Chỉ từ loại động từ mới được có verb forms."
            )

        form_types = [
            form["form_type"]
            for form in forms_data
        ]

        if len(form_types) != len(set(form_types)):
            raise ValueError(
                "Không được có nhiều form cùng loại."
            )

    @staticmethod
    @transaction.atomic
    def create(
        *,
        data,
        forms=None,
        synonyms=None,
        sources=None,
    ):
        forms = forms or []
        synonyms = synonyms or []
        sources = sources or []

        vocabulary = Vocabulary.objects.create(
            **data
        )

        VocabularyService._validate_forms(
            vocabulary,
            forms,
        )

        VocabularyForm.objects.bulk_create(
            [
                VocabularyForm(
                    vocabulary=vocabulary,
                    **form,
                )
                for form in forms
            ]
        )

        vocabulary.synonyms.set(
            synonyms
        )

        vocabulary.sources.set(
            sources
        )

        return vocabulary

    @staticmethod
    @transaction.atomic
    def update(
        *,
        vocabulary,
        data,
        forms=None,
        synonyms=None,
        sources=None,
    ):
        old_word_type = vocabulary.word_type

        for field, value in data.items():
            setattr(
                vocabulary,
                field,
                value,
            )

        vocabulary.version += 1

        vocabulary.save()

        new_word_type = vocabulary.word_type

        # Nếu đổi từ verb sang loại khác,
        # các verb forms không còn hợp lệ.
        if (
            str(old_word_type).startswith("verb")
            and not str(new_word_type).startswith("verb")
            and forms is None
        ):
            vocabulary.forms.all().delete()

        if forms is not None:
            VocabularyService._validate_forms(
                vocabulary,
                forms,
            )

            vocabulary.forms.all().delete()

            VocabularyForm.objects.bulk_create(
                [
                    VocabularyForm(
                        vocabulary=vocabulary,
                        **form,
                    )
                    for form in forms
                ]
            )

        if synonyms is not None:
            vocabulary.synonyms.set(
                synonyms
            )

        if sources is not None:
            vocabulary.sources.set(
                sources
            )

        return vocabulary


class GrammarService:

    @staticmethod
    @transaction.atomic
    def create(
        *,
        data,
        sources=None,
    ):
        sources = sources or []

        grammar = Grammar.objects.create(
            **data
        )

        grammar.sources.set(
            sources
        )

        return grammar

    @staticmethod
    @transaction.atomic
    def update(
        *,
        grammar,
        data,
        sources=None,
    ):
        for field, value in data.items():
            setattr(
                grammar,
                field,
                value,
            )

        grammar.version += 1

        grammar.save()

        if sources is not None:
            grammar.sources.set(
                sources
            )

        return grammar


class SourceService:

    @staticmethod
    @transaction.atomic
    def create(
        *,
        data,
    ):
        return Source.objects.create(
            **data
        )

    @staticmethod
    @transaction.atomic
    def update(
        *,
        source,
        data,
    ):
        for field, value in data.items():
            setattr(
                source,
                field,
                value,
            )

        source.save()

        return source