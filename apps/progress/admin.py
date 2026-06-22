from django.contrib import admin

from .models import UserProgress


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "status", "times_seen", "last_seen")
    list_filter = ("status",)
    search_fields = ("user__email", "word__text")
