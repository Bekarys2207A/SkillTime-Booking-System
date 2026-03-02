from django.contrib import admin
from .models import Lesson, LessonSlot

# Register your models here.

class LessonSlotInline(admin.TabularInline):
    model = LessonSlot
    extra = 0
    fields = ("starts_at", "ends_at", "status", "held_by", "held_until")
    readonly_fields = ("status", "held_by", "held_until")  


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "is_active", "created_at")
    list_filter = ("is_active", "teacher")
    search_fields = ("title", "description", "teacher__email")
    ordering = ("-created_at",)

    inlines = [LessonSlotInline]

    def has_delete_permission(self, request, obj=None):
        return request.user.role == "admin"