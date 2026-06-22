from django.contrib import admin

from .models import AIUsage


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "session_key", "word", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "session_key", "word__text")
