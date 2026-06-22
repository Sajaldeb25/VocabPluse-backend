from django.contrib import admin

from .models import Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "currency", "duration_days", "is_active")
    list_filter = ("is_active", "currency")
    prepopulated_fields = {"slug": ("name",)}


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("transaction_id", "gateway", "amount", "status", "created_at")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "start_at", "end_at")
    list_filter = ("status", "plan")
    search_fields = ("user__email",)
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "subscription", "amount", "status", "created_at")
    list_filter = ("status", "gateway")
    search_fields = ("transaction_id", "subscription__user__email")
