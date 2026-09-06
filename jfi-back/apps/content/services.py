import csv
import io
import json

from django.db import transaction
from openpyxl import load_workbook

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


VOCABULARY_REQUIRED_COLUMNS = {
    "kanji",
    "hiragana",
    "meaning",
    "type",
    "level",
}

GRAMMAR_REQUIRED_COLUMNS = {
    "pattern",
    "meaning",
    "level",
}


class ImportResult:
    def __init__(self):
        self.total = 0
        self.imported = 0
        self.skipped = 0
        self.failed = 0
        self.errors = []

    def add_error(self, row, message):
        self.failed += 1
        self.errors.append(
            {
                "row": row,
                "message": message,
            }
        )


def _normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def _read_csv(file):
    raw = file.read()

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig")

    reader = csv.DictReader(
        io.StringIO(raw)
    )

    return list(reader)


def _read_xlsx(file):
    workbook = load_workbook(
        filename=file,
        read_only=True,
        data_only=True,
    )

    worksheet = workbook.active

    rows = list(
        worksheet.iter_rows(
            values_only=True
        )
    )

    if not rows:
        return []

    headers = [
        _normalize(value)
        for value in rows[0]
    ]

    result = []

    for row in rows[1:]:
        result.append(
            {
                headers[index]: value
                for index, value in enumerate(row)
                if index < len(headers)
                and headers[index]
            }
        )

    return result


def _read_json(file):
    raw = file.read()

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig")
    new_data = []
    try:
        data = json.loads(raw)
        data = data["vocab"]
        
        for item in data:
            new_item = {
                "kanji": item.get("word", ""),
                "hiragana": item.get("reading", ""),
                "han_viet": item.get("han_viet", ""),
                "meaning": item.get("meaning", ""),
                "type": item.get("type", "noun"),
                "level": item.get("level", "N3"),
                "example": item.get("example_jp", ""),
                "source": [
                "jlpt180.com"
                ],
                "forms": []
            }
            new_data.append(new_item)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON không hợp lệ: {exc}"
        ) from exc

    if not isinstance(new_data, list):
        raise ValueError(
            "JSON phải có dạng array."
        )

    return new_data


def read_import_file(file):
    filename = file.name.lower()

    if filename.endswith(".csv"):
        return _read_csv(file)

    if filename.endswith(".xlsx"):
        return _read_xlsx(file)

    if filename.endswith(".json"):
        return _read_json(file)

    raise ValueError(
        "Chỉ hỗ trợ CSV, XLSX hoặc JSON."
    )


def _validate_level(level):
    valid_levels = {
        choice[0]
        for choice in JLPTLevel.choices
    }

    if level not in valid_levels:
        raise ValueError(
            f"Level không hợp lệ: {level}"
        )


def _validate_word_type(word_type):
    valid_types = {
        choice[0]
        for choice in WordType.choices
    }

    if word_type not in valid_types:
        raise ValueError(
            f"Type không hợp lệ: {word_type}"
        )


def _get_sources(values):
    if not values:
        return []

    if isinstance(values, str):
        values = [
            item.strip()
            for item in values.split(",")
            if item.strip()
        ]

    if not isinstance(values, list):
        raise ValueError(
            "source phải là list hoặc string."
        )

    sources = []

    for value in values:
        name = _normalize(value)

        if not name:
            continue

        source, _ = Source.objects.get_or_create(
            name=name
        )

        sources.append(source)

    return sources


def _get_form_value(row, key):
    return _normalize(
        row.get(key)
    )


def _import_verb_forms(
    vocabulary,
    row,
):
    if vocabulary.word_type != WordType.VERB:
        return

    forms = row.get("forms")

    # JSON format
    if forms is not None:
        if not isinstance(forms, list):
            raise ValueError(
                "forms phải là list."
            )

        for form in forms:
            if not isinstance(form, dict):
                raise ValueError(
                    "Mỗi form phải là object."
                )

            form_type = _normalize(
                form.get("type")
            )

            value = _normalize(
                form.get("value")
            )

            if not form_type or not value:
                continue

            valid_types = {
                choice[0]
                for choice in VerbFormType.choices
            }

            if form_type not in valid_types:
                raise ValueError(
                    f"Verb form không hợp lệ: "
                    f"{form_type}"
                )

            VocabularyForm.objects.update_or_create(
                vocabulary=vocabulary,
                form_type=form_type,
                defaults={
                    "value": value,
                },
            )

        return

    # CSV / XLSX format
    form_columns = {
        "dictionary": VerbFormType.DICTIONARY,
        "masu": VerbFormType.MASU,
        "nai": VerbFormType.NAI,
        "ta": VerbFormType.TA,
        "te": VerbFormType.TE,
        "nakatta": VerbFormType.NAKATTA,
        "potential": VerbFormType.POTENTIAL,
        "passive": VerbFormType.PASSIVE,
        "causative": VerbFormType.CAUSATIVE,
        "imperative": VerbFormType.IMPERATIVE,
    }

    for column, form_type in form_columns.items():
        value = _get_form_value(
            row,
            column,
        )

        if not value:
            continue

        VocabularyForm.objects.update_or_create(
            vocabulary=vocabulary,
            form_type=form_type,
            defaults={
                "value": value,
            },
        )


def import_vocabularies(rows):
    result = ImportResult()

    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        result.total += 1

        try:
            row = {
                str(key).strip().lower(): value
                for key, value in row.items()
                if key is not None
            }

            missing = [
                column
                for column in VOCABULARY_REQUIRED_COLUMNS
                if not _normalize(
                    row.get(column)
                )
            ]

            if missing:
                raise ValueError(
                    "Thiếu dữ liệu: "
                    + ", ".join(missing)
                )

            kanji = _normalize(
                row.get("kanji")
            )
            hiragana = _normalize(
                row.get("hiragana")
            )
            han_viet = _normalize(
                row.get("han_viet")
            )
            meaning = _normalize(
                row.get("meaning")
            )
            word_type = _normalize(
                row.get("type")
            ).lower()
            level = _normalize(
                row.get("level")
            ).upper()
            example = _normalize(
                row.get("example")
            )

            _validate_level(level)
            _validate_word_type(word_type)

            vocabulary = Vocabulary.objects.filter(
                kanji=kanji
            ).first()

            if vocabulary:
                sources = _get_sources(
                    row.get("source")
                )

                vocabulary.sources.add(
                    *sources
                )

                _import_verb_forms(
                    vocabulary,
                    row,
                )

                result.skipped += 1
                continue

            with transaction.atomic():
                vocabulary = Vocabulary.objects.create(
                    kanji=kanji,
                    hiragana=hiragana,
                    han_viet=han_viet,
                    meaning=meaning,
                    word_type=word_type,
                    level=level,
                    example=example,
                    status=ContentStatus.UPLOAD,
                )

                sources = _get_sources(
                    row.get("source")
                )

                vocabulary.sources.add(
                    *sources
                )

                _import_verb_forms(
                    vocabulary,
                    row,
                )

            result.imported += 1

        except Exception as exc:
            result.add_error(
                row_number,
                str(exc),
            )

    return result


def import_grammars(rows):
    result = ImportResult()

    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        result.total += 1

        try:
            row = {
                str(key).strip().lower(): value
                for key, value in row.items()
                if key is not None
            }

            missing = [
                column
                for column in GRAMMAR_REQUIRED_COLUMNS
                if not _normalize(
                    row.get(column)
                )
            ]

            if missing:
                raise ValueError(
                    "Thiếu dữ liệu: "
                    + ", ".join(missing)
                )

            pattern = _normalize(
                row.get("pattern")
            )
            meaning = _normalize(
                row.get("meaning")
            )
            level = _normalize(
                row.get("level")
            ).upper()
            example = _normalize(
                row.get("example")
            )

            _validate_level(level)

            grammar = Grammar.objects.filter(
                pattern=pattern
            ).first()

            if grammar:
                sources = _get_sources(
                    row.get("source")
                )

                grammar.sources.add(
                    *sources
                )

                result.skipped += 1
                continue

            with transaction.atomic():
                grammar = Grammar.objects.create(
                    pattern=pattern,
                    meaning=meaning,
                    level=level,
                    example=example,
                    status=ContentStatus.UPLOAD,
                )

                sources = _get_sources(
                    row.get("source")
                )

                grammar.sources.add(
                    *sources
                )

            result.imported += 1

        except Exception as exc:
            result.add_error(
                row_number,
                str(exc),
            )

    return result