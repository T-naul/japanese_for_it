# pyrefly: ignore [missing-import]
import csv
import io
import json
import uuid
import openpyxl
from django.db import transaction

from .models import (
    ContentStatus,
    Grammar,
    JLPTLevel,
    Source,
    VerbFormType,
    Vocabulary,
    VocabularyForm,
    WordType,
)


class FileImportService:

    @staticmethod
    def parse_file(file_obj):
        """
        Parses JSON, CSV, or XLSX file objects into a list of dictionaries.
        """
        filename = getattr(file_obj, "name", "").lower()

        if filename.endswith(".json"):
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            data = json.loads(content)
            if isinstance(data, dict):
                data = (
                    data.get("vocabularies")
                    or data.get("grammars")
                    or data.get("items")
                    or [data]
                )
            if not isinstance(data, list):
                raise ValueError("JSON content must be a list of items or contain a list key.")
            return data

        elif filename.endswith(".csv"):
            content = file_obj.read()
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8-sig")
                except UnicodeDecodeError:
                    content = content.decode("latin-1")
            f = io.StringIO(content)
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]

        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            content = file_obj.read()
            wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [
                str(h).strip().lower() if h is not None else ""
                for h in rows[0]
            ]
            data = []
            for row in rows[1:]:
                if not any(cell is not None and str(cell).strip() != "" for cell in row):
                    continue
                row_dict = {}
                for col_idx, cell_val in enumerate(row):
                    if col_idx < len(headers) and headers[col_idx]:
                        row_dict[headers[col_idx]] = (
                            str(cell_val).strip() if cell_val is not None else ""
                        )
                data.append(row_dict)
            return data

        else:
            raise ValueError(
                "Định dạng file không được hỗ trợ. Vui lòng tải lên file .json, .csv, hoặc .xlsx."
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

    @staticmethod
    def import_from_file(file_obj):
        parsed_data = FileImportService.parse_file(file_obj)
        valid_jlpt = set(JLPTLevel.values)
        valid_word_types = set(WordType.values)
        valid_statuses = set(ContentStatus.values)
        valid_verb_forms = set(VerbFormType.values)

        errors = []
        valid_vocabs = []
        valid_forms = []

        for idx, item in enumerate(parsed_data, start=1):
            row_errors = []
            kanji = str(item.get("kanji", "") or "").strip()
            hiragana = str(item.get("hiragana", "") or "").strip()
            meaning = str(item.get("meaning", "") or "").strip()
            han_viet = str(item.get("han_viet", "") or "").strip()
            example = str(item.get("example", "") or "").strip()

            word_type = str(item.get("word_type", "") or "verb_1").strip().lower()
            if not word_type:
                word_type = "verb_1"
            elif word_type == "verb":
                word_type = "verb_1"

            level = str(item.get("level", "") or "N3").strip().upper()
            if not level:
                level = "N3"

            status_val = str(item.get("status", "") or "upload").strip().lower()
            if not status_val:
                status_val = "upload"

            if not kanji:
                row_errors.append("Thiếu trường bắt buộc: 'kanji'.")
            if not hiragana:
                row_errors.append("Thiếu trường bắt buộc: 'hiragana'.")
            if not meaning:
                row_errors.append("Thiếu trường bắt buộc: 'meaning'.")

            if word_type not in valid_word_types:
                row_errors.append(
                    f"Loại từ '{word_type}' không hợp lệ. Phải là một trong: {', '.join(valid_word_types)}."
                )

            if level not in valid_jlpt:
                row_errors.append(
                    f"Trình độ JLPT '{level}' không hợp lệ. Phải là một trong: {', '.join(valid_jlpt)}."
                )

            if status_val not in valid_statuses:
                row_errors.append(
                    f"Trạng thái '{status_val}' không hợp lệ. Phải là một trong: {', '.join(valid_statuses)}."
                )

            # Parse forms if provided
            raw_forms = item.get("forms", [])
            forms_list = []
            if isinstance(raw_forms, str) and raw_forms.strip():
                try:
                    raw_forms = json.loads(raw_forms)
                except Exception:
                    row_errors.append("Định dạng 'forms' dạng JSON không hợp lệ.")

            if isinstance(raw_forms, list):
                seen_types = set()
                for f in raw_forms:
                    if isinstance(f, dict) and "form_type" in f and "value" in f:
                        ft = str(f["form_type"]).strip().lower()
                        fv = str(f["value"]).strip()
                        if ft not in valid_verb_forms:
                            row_errors.append(f"Loại thể động từ '{ft}' không hợp lệ.")
                        elif ft in seen_types:
                            row_errors.append(f"Loại thể động từ '{ft}' bị lặp lại trong cùng một từ.")
                        elif fv:
                            seen_types.add(ft)
                            forms_list.append({"form_type": ft, "value": fv})

            if not word_type.startswith("verb") and forms_list:
                row_errors.append("Chỉ từ loại động từ mới được có verb forms.")

            if row_errors:
                errors.append({"row": idx, "kanji": kanji or "N/A", "errors": row_errors})
                continue

            vocab_id = uuid.uuid4()
            vocab_obj = Vocabulary(
                id=vocab_id,
                kanji=kanji,
                hiragana=hiragana,
                han_viet=han_viet,
                meaning=meaning,
                word_type=word_type,
                level=level,
                status=status_val,
                example=example,
            )
            valid_vocabs.append(vocab_obj)

            if word_type.startswith("verb"):
                for form_item in forms_list:
                    valid_forms.append(
                        VocabularyForm(
                            vocabulary_id=vocab_id,
                            form_type=form_item["form_type"],
                            value=form_item["value"],
                        )
                    )

        if valid_vocabs:
            with transaction.atomic():
                Vocabulary.objects.bulk_create(valid_vocabs, batch_size=500)
                if valid_forms:
                    VocabularyForm.objects.bulk_create(valid_forms, batch_size=500)

        return {
            "total_rows": len(parsed_data),
            "created_count": len(valid_vocabs),
            "error_count": len(errors),
            "errors": errors,
        }


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

    @staticmethod
    def import_from_file(file_obj):
        parsed_data = FileImportService.parse_file(file_obj)
        valid_jlpt = set(JLPTLevel.values)
        valid_statuses = set(ContentStatus.values)

        errors = []
        valid_grammars = []

        for idx, item in enumerate(parsed_data, start=1):
            row_errors = []
            pattern = str(item.get("pattern", "") or "").strip()
            meaning = str(item.get("meaning", "") or "").strip()
            example = str(item.get("example", "") or "").strip()
            explanation = str(item.get("explanation", "") or "").strip()

            level = str(item.get("level", "") or "N3").strip().upper()
            if not level:
                level = "N3"

            status_val = str(item.get("status", "") or "upload").strip().lower()
            if not status_val:
                status_val = "upload"

            if not pattern:
                row_errors.append("Thiếu trường bắt buộc: 'pattern'.")
            if not meaning:
                row_errors.append("Thiếu trường bắt buộc: 'meaning'.")

            if level not in valid_jlpt:
                row_errors.append(
                    f"Trình độ JLPT '{level}' không hợp lệ. Phải là một trong: {', '.join(valid_jlpt)}."
                )

            if status_val not in valid_statuses:
                row_errors.append(
                    f"Trạng thái '{status_val}' không hợp lệ. Phải là một trong: {', '.join(valid_statuses)}."
                )

            if row_errors:
                errors.append({"row": idx, "pattern": pattern or "N/A", "errors": row_errors})
                continue

            grammar_obj = Grammar(
                id=uuid.uuid4(),
                pattern=pattern,
                meaning=meaning,
                level=level,
                status=status_val,
                example=example,
                explanation=explanation,
            )
            valid_grammars.append(grammar_obj)

        if valid_grammars:
            with transaction.atomic():
                Grammar.objects.bulk_create(valid_grammars, batch_size=500)

        return {
            "total_rows": len(parsed_data),
            "created_count": len(valid_grammars),
            "error_count": len(errors),
            "errors": errors,
        }


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
