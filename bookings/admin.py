from django.contrib import admin
from .models import Booking

# Register your models here.

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "lesson", "slot", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email",)
    ordering = ("-created_at",)
    
    readonly_fields = ("user", "lesson", "slot", "starts_at", "ends_at", "status", "created_at")

    def has_add_permission(self, request):
        return False  

    def has_delete_permission(self, request, obj=None):
        return request.user.role == "admin"

    def has_change_permission(self, request, obj=None):
        return request.user.role == "admin"