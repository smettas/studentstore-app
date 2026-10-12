from django.contrib import admin, messages
from .models import Notification, PushDevice
from .services.expo_push import send_notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "user__mobile")
    readonly_fields = ("created_at",)
    actions = ("send_selected_push",)

    @admin.action(description="Send selected notifications via Expo (manual)")
    def send_selected_push(self, request, queryset):
        total = 0
        for notification in queryset.select_related("user"):
            total += len(send_notification(notification))
        self.message_user(request, f"Expo returned {total} push ticket(s). Delivery is not guaranteed.", messages.INFO)


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("user__mobile", "expo_push_token")
