from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Lesson
from .serializers import LessonSerializer, HoldSlotSerializer
from .permissions import IsTeacherOrAdmin, IsClientUserOrAdmin
from .utils import invalidate_lesson_cache, invalidate_availability_cache
from .services import AvailabilityService, SlotHoldService
from .cache_keys import lessons_list_key, lesson_detail_key


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "availability"]:
            return [AllowAny()]
        if self.action in ["hold"]:
            return [IsAuthenticated(), IsClientUserOrAdmin()]
        return [IsTeacherOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == "admin":
                return Lesson.objects.all()
            if user.role == "teacher":
                return Lesson.objects.filter(teacher=user)
        return Lesson.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        key = lessons_list_key()
        cached = cache.get(key)

        if cached:
            return Response(cached)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        cache.set(key, serializer.data, timeout=300)  

        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        lesson_id = kwargs.get("pk")
        key = lesson_detail_key(lesson_id)

        cached = cache.get(key)
        if cached:
            return Response(cached)

        instance = self.get_object()
        serializer = self.get_serializer(instance)

        cache.set(key, serializer.data, timeout=300) 

        return Response(serializer.data)

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

    @action(detail=True, methods=["patch"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        lesson = self.get_object()
        lesson.is_active = False
        lesson.save(update_fields=["is_active"])
        invalidate_lesson_cache(lesson.id)
        return Response({"detail": "Lesson deactivated"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        date = request.query_params.get("date")
        if not date:
            raise ValidationError({"date": "Query param 'date' is required (YYYY-MM-DD)"})

        try:
            slots = AvailabilityService.get_availability(int(pk), date)
        except ValueError as e:
            raise ValidationError({"date": str(e)})

        return Response({
            "lesson_id": int(pk),
            "date": date,
            "available_slots": slots
        })

    @action(detail=True, methods=["post"], url_path="hold")
    def hold(self, request, pk=None):
        serializer = HoldSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slot_id = serializer.validated_data["slot_id"]

        slot = SlotHoldService.hold_slot(
            user=request.user,
            lesson_id=int(pk),
            slot_id=slot_id,
        )

        date_str = slot.starts_at.date().isoformat()
        invalidate_availability_cache(
            lesson_id=int(pk),
            date_str=date_str
        )

        return Response({
            "detail": "Slot held",
            "lesson_id": int(pk),
            "slot_id": slot.id,
            "status": slot.status,
            "held_until": slot.held_until.isoformat() if slot.held_until else None,
        }, status=status.HTTP_200_OK)