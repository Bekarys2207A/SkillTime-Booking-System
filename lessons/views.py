from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Lesson, LessonSlot
from .serializers import LessonSerializer, HoldSlotSerializer, AvailabilityQuerySerializer, LessonSlotCreateSerializer, LessonSlotSerializer
from .permissions import IsTeacherOrAdmin, IsClientUserOrAdmin
from .utils import invalidate_lesson_cache, invalidate_availability_cache
from .services import AvailabilityService, SlotHoldService
from .cache_keys import lessons_list_key, lesson_detail_key
from skilltime.api.schema_serializers import ErrorResponseSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Lessons"],
        summary="List lessons",
        description="Public list of active lessons. Teachers see their lessons; admin sees all.",
        responses={200: LessonSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Lessons"],
        summary="Get lesson detail",
        responses={200: LessonSerializer, 404: ErrorResponseSerializer},
    ),
    create=extend_schema(tags=["Lessons"], summary="Create lesson", responses={201: LessonSerializer}),
    update=extend_schema(tags=["Lessons"], summary="Update lesson", responses={200: LessonSerializer}),
    partial_update=extend_schema(tags=["Lessons"], summary="Partial update lesson", responses={200: LessonSerializer}),
    destroy=extend_schema(tags=["Lessons"], summary="Delete lesson", responses={204: None}),
)
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

    @extend_schema(
        tags=["Lessons"],
        summary="Deactivate lesson",
        responses={200: OpenApiTypes.OBJECT, 403: ErrorResponseSerializer, 404: ErrorResponseSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        lesson = self.get_object()
        lesson.is_active = False
        lesson.save(update_fields=["is_active"])
        invalidate_lesson_cache(lesson.id)
        return Response({"detail": "Lesson deactivated"}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Lessons"],
        summary="Get lesson availability for a date",
        parameters=[
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                required=True,
                description="YYYY-MM-DD",
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Example response",
                value={
                    "lesson_id": 3,
                    "date": "2026-03-10",
                    "available_slots": [
                        {"id": 1, "starts_at": "2026-03-10T10:00:00+05:00", "ends_at": "2026-03-10T11:00:00+05:00"}
                    ],
                },
            )
        ],
    )
    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        qp = AvailabilityQuerySerializer(data=request.query_params)
        qp.is_valid(raise_exception=True)
        date = qp.validated_data["date"].isoformat()

        slots = AvailabilityService.get_availability(int(pk), date)
        return Response({"lesson_id": int(pk), "date": date, "available_slots": slots})

    @extend_schema(
        tags=["Lessons"],
        summary="Hold a slot",
        request=HoldSlotSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
    )
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
        invalidate_availability_cache(lesson_id=int(pk), date_str=date_str)

        return Response(
            {
                "detail": "Slot held",
                "lesson_id": int(pk),
                "slot_id": slot.id,
                "status": slot.status,
                "held_until": slot.held_until.isoformat() if slot.held_until else None,
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=True, methods=["get", "post"], url_path="slots")
    @extend_schema(
        tags=["Slots"],
        summary="List/create lesson slots (teacher/admin)",
        description="GET returns slots list. POST creates a new slot for the lesson.",
        request=LessonSlotCreateSerializer,
        responses={200: LessonSlotSerializer(many=True), 201: LessonSlotSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
    )
    def slots(self, request, pk=None):
        lesson = self.get_object()

        if request.user.role == "teacher" and lesson.teacher != request.user:
            raise PermissionDenied("You can manage slots only for your own lessons.")

        if request.method == "GET":
            qs = LessonSlot.objects.filter(lesson=lesson).order_by("starts_at")
            return Response(LessonSlotSerializer(qs, many=True).data, status=status.HTTP_200_OK)

        serializer = LessonSlotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            slot = LessonSlot.objects.create(
                lesson=lesson,
                starts_at=serializer.validated_data["starts_at"],
                ends_at=serializer.validated_data["ends_at"],
                status=LessonSlot.STATUS_AVAILABLE,
            )
        except Exception as e:
            raise ValidationError({"detail": str(e)})

        return Response(LessonSlotSerializer(slot).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["delete"], url_path=r"slots/(?P<slot_id>\d+)")
    @extend_schema(
        tags=["Slots"],
        summary="Delete lesson slot (teacher/admin)",
        responses={204: None, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
    )
    def delete_slot(self, request, pk=None, slot_id=None):
        lesson = self.get_object()

        if request.user.role == "teacher" and lesson.teacher != request.user:
            raise PermissionDenied("You can delete slots only for your own lessons.")

        slot = LessonSlot.objects.filter(id=slot_id, lesson=lesson).first()
        if not slot:
            raise ValidationError({"detail": "Slot not found."})

        if slot.status != LessonSlot.STATUS_AVAILABLE:
            raise ValidationError({"detail": f"Cannot delete slot with status '{slot.status}'."})

        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)