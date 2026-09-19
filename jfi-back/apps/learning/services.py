# apps/learning/services.py

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.content.models import Grammar, Vocabulary
from apps.users.models import UserGrammar, UserVocabulary

from .models import (
    DayGrammar,
    DayVocabulary,
    StudyPlan,
    StudyPlanDay,
    StudyPlanStatus,
)


class StudyPlanService:

    @staticmethod
    def _distribute(total, days):
        """
        Chia total item đều cho days ngày.

        Ví dụ:
            10 / 3 -> [4, 3, 3]
        """

        if days <= 0:
            raise ValueError(
                "Số ngày học phải lớn hơn 0."
            )

        base = total // days
        remainder = total % days

        return [
            base + (1 if index < remainder else 0)
            for index in range(days)
        ]

    @staticmethod
    def _get_unlearned_vocabulary(user, level):
        """
        Lấy vocabulary thuộc level mà user chưa học.
        """

        learned_ids = UserVocabulary.objects.filter(
            user=user,
            learned_at__isnull=False,
        ).values_list(
            "vocabulary_id",
            flat=True,
        )

        return Vocabulary.objects.filter(
            level=level,
            status="accepted",
        ).exclude(
            id__in=learned_ids,
        ).order_by(
            "created_at",
            "id",
        )

    @staticmethod
    def _get_unlearned_grammar(user, level):
        """
        Lấy grammar thuộc level mà user chưa học.
        """

        learned_ids = UserGrammar.objects.filter(
            user=user,
            learned_at__isnull=False,
        ).values_list(
            "grammar_id",
            flat=True,
        )

        return Grammar.objects.filter(
            level=level,
            status="accepted",
        ).exclude(
            id__in=learned_ids,
        ).order_by(
            "created_at",
            "id",
        )

    @classmethod
    @transaction.atomic
    def create_plan(
        cls,
        user,
        level,
        total_days,
        start_date=None,
    ):
        """
        Tạo một StudyPlan mới.

        Mỗi ngày có tập Vocabulary/Grammar riêng.
        Không carry-over sang ngày tiếp theo.
        """

        if total_days <= 0:
            raise ValueError(
                "Số ngày học phải lớn hơn 0."
            )

        if start_date is None:
            start_date = timezone.localdate()

        # Chỉ cho phép một plan active
        # tại một thời điểm.
        if StudyPlan.objects.filter(
            user=user,
            status=StudyPlanStatus.ACTIVE,
        ).exists():
            raise ValueError(
                "User đang có StudyPlan active."
            )

        vocabularies = list(
            cls._get_unlearned_vocabulary(
                user=user,
                level=level,
            )
        )

        grammars = list(
            cls._get_unlearned_grammar(
                user=user,
                level=level,
            )
        )

        vocabulary_distribution = cls._distribute(
            len(vocabularies),
            total_days,
        )

        grammar_distribution = cls._distribute(
            len(grammars),
            total_days,
        )

        plan = StudyPlan.objects.create(
            user=user,
            level=level,
            total_days=total_days,
            start_date=start_date,
            status=StudyPlanStatus.ACTIVE,
        )

        vocabulary_index = 0
        grammar_index = 0

        for day_number in range(
            1,
            total_days + 1,
        ):
            day_date = (
                start_date
                + timedelta(
                    days=day_number - 1
                )
            )

            plan_day = StudyPlanDay.objects.create(
                study_plan=plan,
                day_number=day_number,
                date=day_date,
            )

            vocab_count = vocabulary_distribution[
                day_number - 1
            ]

            grammar_count = grammar_distribution[
                day_number - 1
            ]

            day_vocabularies = vocabularies[
                vocabulary_index:
                vocabulary_index + vocab_count
            ]

            day_grammars = grammars[
                grammar_index:
                grammar_index + grammar_count
            ]

            DayVocabulary.objects.bulk_create(
                [
                    DayVocabulary(
                        study_plan_day=plan_day,
                        vocabulary=vocabulary,
                    )
                    for vocabulary in day_vocabularies
                ]
            )

            DayGrammar.objects.bulk_create(
                [
                    DayGrammar(
                        study_plan_day=plan_day,
                        grammar=grammar,
                    )
                    for grammar in day_grammars
                ]
            )

            vocabulary_index += vocab_count
            grammar_index += grammar_count

        return plan


class LearningService:

    @staticmethod
    def get_day_content(
        user,
        study_plan_day,
    ):
        """
        Chỉ lấy nội dung thuộc đúng ngày này.

        Không lấy nội dung của ngày trước
        hoặc ngày sau.
        """

        if study_plan_day.study_plan.user_id != user.id:
            raise ValueError(
                "StudyPlan không thuộc user này."
            )

        vocabularies = (
            DayVocabulary.objects
            .filter(
                study_plan_day=study_plan_day,
            )
            .select_related("vocabulary")
        )

        grammars = (
            DayGrammar.objects
            .filter(
                study_plan_day=study_plan_day,
            )
            .select_related("grammar")
        )

        return {
            "vocabularies": [
                item.vocabulary
                for item in vocabularies
            ],
            "grammars": [
                item.grammar
                for item in grammars
            ],
        }

    @staticmethod
    @transaction.atomic
    def mark_vocabulary_learned(
        user,
        vocabulary,
    ):
        """
        Đánh dấu Vocabulary đã học.
        """

        progress, created = (
            UserVocabulary.objects.get_or_create(
                user=user,
                vocabulary=vocabulary,
            )
        )

        if progress.learned_at is None:
            progress.learned_at = timezone.now()

            progress.save(
                update_fields=[
                    "learned_at",
                    "updated_at",
                ]
            )

        return progress

    @staticmethod
    @transaction.atomic
    def mark_grammar_learned(
        user,
        grammar,
    ):
        """
        Đánh dấu Grammar đã học.
        """

        progress, created = (
            UserGrammar.objects.get_or_create(
                user=user,
                grammar=grammar,
            )
        )

        if progress.learned_at is None:
            progress.learned_at = timezone.now()

            progress.save(
                update_fields=[
                    "learned_at",
                    "updated_at",
                ]
            )

        return progress


class ProgressService:

    @staticmethod
    def get_day_progress(
        user,
        study_plan_day,
    ):
        """
        Tính progress của đúng một ngày.
        """

        if study_plan_day.study_plan.user_id != user.id:
            raise ValueError(
                "StudyPlan không thuộc user này."
            )

        vocabulary_ids = list(
            study_plan_day.vocabularies.values_list(
                "vocabulary_id",
                flat=True,
            )
        )

        grammar_ids = list(
            study_plan_day.grammars.values_list(
                "grammar_id",
                flat=True,
            )
        )

        total_vocabulary = len(
            vocabulary_ids
        )

        total_grammar = len(
            grammar_ids
        )

        learned_vocabulary = (
            UserVocabulary.objects.filter(
                user=user,
                vocabulary_id__in=vocabulary_ids,
                learned_at__isnull=False,
            ).count()
        )

        learned_grammar = (
            UserGrammar.objects.filter(
                user=user,
                grammar_id__in=grammar_ids,
                learned_at__isnull=False,
            ).count()
        )

        total = (
            total_vocabulary
            + total_grammar
        )

        learned = (
            learned_vocabulary
            + learned_grammar
        )

        remaining = total - learned

        percentage = (
            round(
                learned / total * 100,
                2,
            )
            if total > 0
            else 100
        )

        completed = (
            total == learned
        )

        return {
            "total": total,
            "learned": learned,
            "remaining": remaining,
            "percentage": percentage,
            "completed": completed,
            "vocabulary": {
                "total": total_vocabulary,
                "learned": learned_vocabulary,
                "remaining": (
                    total_vocabulary
                    - learned_vocabulary
                ),
            },
            "grammar": {
                "total": total_grammar,
                "learned": learned_grammar,
                "remaining": (
                    total_grammar
                    - learned_grammar
                ),
            },
        }

    @staticmethod
    def get_plan_progress(
        user,
        study_plan,
    ):
        """
        Tính progress của toàn bộ StudyPlan
        dựa trên từng StudyPlanDay.
        """

        if study_plan.user_id != user.id:
            raise ValueError(
                "StudyPlan không thuộc user này."
            )

        days = list(
            study_plan.days.all()
        )

        day_progress = []

        total_items = 0
        learned_items = 0
        completed_days = 0

        for day in days:
            progress = (
                ProgressService.get_day_progress(
                    user=user,
                    study_plan_day=day,
                )
            )

            day_progress.append(
                {
                    "day_number": day.day_number,
                    "date": day.date,
                    **progress,
                }
            )

            total_items += progress["total"]
            learned_items += progress["learned"]

            if progress["completed"]:
                completed_days += 1

        total_days = len(days)

        overall_percentage = (
            round(
                learned_items
                / total_items
                * 100,
                2,
            )
            if total_items > 0
            else 100
        )

        return {
            "total_days": total_days,
            "completed_days": completed_days,
            "remaining_days": (
                total_days
                - completed_days
            ),
            "total_items": total_items,
            "learned_items": learned_items,
            "remaining_items": (
                total_items
                - learned_items
            ),
            "percentage": overall_percentage,
            "days": day_progress,
        }