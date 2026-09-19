# pyrefly: ignore [missing-import]
from rest_framework import serializers

from .models import (
    ContentStatus,
    Grammar,
    Source,
    Vocabulary,
    VocabularyForm,
)
from .services import (
    GrammarService,
    SourceService,
    VocabularyService,
)


class SourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Source
        fields = [
            "id",
            "name",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


class VocabularyFormSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = VocabularyForm
        fields = [
            "id",
            "form_type",
            "value",
        ]

        read_only_fields = [
            "id",
        ]


class VocabularyListSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Vocabulary
        fields = [
            "id",
            "kanji",
            "hiragana",
            "han_viet",
            "meaning",
            "word_type",
            "level",
            "status",
            "version",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "version",
            "created_at",
            "updated_at",
        ]


class VocabularyDetailSerializer(
    serializers.ModelSerializer
):

    forms = VocabularyFormSerializer(
        many=True,
        required=False,
    )

    synonyms = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Vocabulary.objects.all(),
        required=False,
    )

    sources = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Source.objects.all(),
        required=False,
    )

    class Meta:
        model = Vocabulary

        fields = [
            "id",
            "kanji",
            "hiragana",
            "han_viet",
            "meaning",
            "word_type",
            "level",
            "example",
            "forms",
            "synonyms",
            "sources",
            "status",
            "version",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "version",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """
        Business validation ở tầng API.
        """

        word_type = attrs.get(
            "word_type",
            getattr(
                self.instance,
                "word_type",
                None,
            ),
        )

        forms = attrs.get(
            "forms",
            None,
        )

        # Nếu request có forms thì kiểm tra.
        if forms is not None:

            if word_type != "verb" and not str(word_type).startswith("verb"):
                raise serializers.ValidationError(
                    {
                        "forms": (
                            "Chỉ động từ mới được "
                            "có verb forms."
                        )
                    }
                )

            form_types = [
                form["form_type"]
                for form in forms
            ]

            if len(form_types) != len(
                set(form_types)
            ):
                raise serializers.ValidationError(
                    {
                        "forms": (
                            "Không được có nhiều "
                            "form cùng loại."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):

        forms = validated_data.pop(
            "forms",
            [],
        )

        synonyms = validated_data.pop(
            "synonyms",
            [],
        )

        sources = validated_data.pop(
            "sources",
            [],
        )

        return VocabularyService.create(
            data=validated_data,
            forms=forms,
            synonyms=synonyms,
            sources=sources,
        )

    def update(
        self,
        instance,
        validated_data,
    ):

        forms = validated_data.pop(
            "forms",
            None,
        )

        synonyms = validated_data.pop(
            "synonyms",
            None,
        )

        sources = validated_data.pop(
            "sources",
            None,
        )

        return VocabularyService.update(
            vocabulary=instance,
            data=validated_data,
            forms=forms,
            synonyms=synonyms,
            sources=sources,
        )


class GrammarSerializer(
    serializers.ModelSerializer
):

    sources = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Source.objects.all(),
        required=False,
    )

    class Meta:
        model = Grammar

        fields = [
            "id",
            "pattern",
            "meaning",
            "level",
            "example",
            "sources",
            "status",
            "version",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "version",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):

        sources = validated_data.pop(
            "sources",
            [],
        )

        return GrammarService.create(
            data=validated_data,
            sources=sources,
        )

    def update(
        self,
        instance,
        validated_data,
    ):

        sources = validated_data.pop(
            "sources",
            None,
        )

        return GrammarService.update(
            grammar=instance,
            data=validated_data,
            sources=sources,
        )