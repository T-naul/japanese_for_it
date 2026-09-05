from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserVocabulary, UserGrammar


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(UserVocabulary)
class UserVocabularyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "vocabulary",
        "learned_at",
    )

    list_filter = ("learned_at",)


@admin.register(UserGrammar)
class UserGrammarAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "grammar",
        "learned_at",
    )

    list_filter = ("learned_at",)