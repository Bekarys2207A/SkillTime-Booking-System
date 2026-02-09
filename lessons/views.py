# lessons/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Lesson
from .serializers import LessonSerializer
from .permissions import IsTeacherOrAdmin
from .utils import invalidate_lesson_cache

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Lesson.objects.all()
        elif user.role == 'teacher':
            return Lesson.objects.filter(teacher=user)
        else:
            return Lesson.objects.filter(is_active=True)

    def perform_create(self, serializer):
        lesson = serializer.save()
        invalidate_lesson_cache(lesson.id)

    def perform_update(self, serializer):
        lesson = serializer.save()
        invalidate_lesson_cache(lesson.id)

    def perform_destroy(self, instance):
        lesson_id = instance.id
        instance.delete()
        invalidate_lesson_cache(lesson_id)

    @action(detail=True, methods=['patch'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        lesson = self.get_object()
        lesson.is_active = False
        lesson.save()
        invalidate_lesson_cache(lesson.id)
        return Response({"detail": "Lesson deactivated"}, status=status.HTTP_200_OK)