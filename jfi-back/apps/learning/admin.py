from django.contrib import admin

from .models import (
    StudyPlan,
    StudyPlanDay,
    DayVocabulary,
    DayGrammar,
)


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "level",
        "total_days",
        "start_date",
        "status",
        "created_at",
    )

    list_filter = (
        "level",
        "status",
    )

    search_fields = (
        "user__username",
    )


@admin.register(StudyPlanDay)
class StudyPlanDayAdmin(admin.ModelAdmin):
    list_display = (
        "study_plan",
        "day_number",
        "date",
    )

    list_filter = ("date",)


@admin.register(DayVocabulary)
class DayVocabularyAdmin(admin.ModelAdmin):
    list_display = (
        "study_plan_day",
        "vocabulary",
        # "is_carry_over",
    )

    # list_filter = ("is_carry_over",)


@admin.register(DayGrammar)
class DayGrammarAdmin(admin.ModelAdmin):
    list_display = (
        "study_plan_day",
        "grammar",
        # "is_carry_over",
    )

    # list_filter = ("is_carry_over",)