from rest_framework.permissions import BasePermission

class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('teacher', 'admin')

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.teacher_id == request.user.id


class IsClientUserOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("user", "admin")