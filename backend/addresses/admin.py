from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("recipient_name", "user", "city", "state", "postal_code", "is_default")
    search_fields = ("recipient_name", "user__mobile", "postal_code")
