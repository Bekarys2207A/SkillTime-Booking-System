# lessons/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from .models import Lesson
from .serializers import LessonSerializer
from .permissions import IsTeacherOrAdmin
from .utils import invalidate_lesson_cache
from .services import AvailabilityService

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "availability"]:
            return [AllowAny()]
        return [IsTeacherOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == "admin":
                return Lesson.objects.all()
            if user.role == "teacher":
                return Lesson.objects.filter(teacher=user)
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
    
    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        date = request.query_params.get("date")

        if not date:
            raise ValidationError({"date": "Query param 'date' is required (YYYY-MM-DD)"})

        try:
            slots = AvailabilityService.get_availability(pk, date)
        except ValueError as e:
            raise ValidationError({"date": str(e)})

        return Response({
            "lesson_id": int(pk),
            "date": date,
            "available_slots": slots,
        })