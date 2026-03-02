from django.contrib import admin
from .models import FileUpload

# Register your models here.

@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "lesson", "mime", "size_bytes", "created_at")
    list_filter = ("mime",)
    search_fields = ("owner__email",)
    ordering = ("-created_at",)

    readonly_fields = ("owner", "lesson", "file", "size_bytes", "mime", "created_at")

    def has_add_permission(self, request):
        return False 