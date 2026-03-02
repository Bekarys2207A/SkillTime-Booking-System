from django.contrib import admin
from .models import AuditLog

# Register your models here.

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("ts", "action", "entity", "entity_id", "actor")
    list_filter = ("action", "entity", "ts")
    search_fields = ("entity_id", "actor__email")
    ordering = ("-ts",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_authenticated and request.user.role == "admin"