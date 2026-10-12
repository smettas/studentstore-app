from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPChallenge

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("id",)
    list_display = ("mobile", "name", "email", "is_staff", "is_active")
    search_fields = ("mobile", "name", "email")
    fieldsets = ((None, {"fields": ("mobile", "password")}), ("Personal", {"fields": ("name", "email")}), ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}), ("Dates", {"fields": ("last_login", "date_joined")}))
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("mobile", "name", "email", "is_staff", "is_active")}),)
    readonly_fields = ("last_login", "date_joined")

@admin.register(OTPChallenge)
class OTPChallengeAdmin(admin.ModelAdmin):
    list_display = ("mobile", "expires_at", "attempts", "verified_at")
    readonly_fields = ("mobile", "code_hash", "expires_at", "attempts", "verified_at", "created_at")
    def has_add_permission(self, request): return False
