from django.contrib import admin
from .models import User, TeacherProfile

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("email",)
    ordering = ("-created_at",)

    def has_delete_permission(self, request, obj=None):
        return request.user.role == "admin"


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "rating")
    search_fields = ("user__email",)