from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import Booking
from .serializers import ConfirmBookingSerializer, BookingListSerializer
from .services import BookingConfirmService, BookingCancelService
from .filters import BookingFilter
from skilltime.api.schema_serializers import ErrorResponseSerializer


class ConfirmBookingView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "confirm"
    
    @extend_schema(
        tags=["Bookings"],
        summary="Confirm booking",
        description="Confirms a held slot. Supports Idempotency-Key header.",
        request=ConfirmBookingSerializer,
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description="Optional idempotency key (max 128 chars).",
            )
        ],
        examples=[
            OpenApiExample(
                "Request example",
                value={"lesson_id": 3, "slot_id": 15},
                request_only=True,
            )
        ],
        responses={200: None, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
    )
    def post(self, request):
        if request.user.role not in ("user", "admin"):
            raise PermissionDenied("Only students can confirm bookings.")

        serializer = ConfirmBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lesson_id = serializer.validated_data["lesson_id"]
        slot_id = serializer.validated_data["slot_id"]

        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key is not None and len(idempotency_key) > 128:
            raise ValidationError({"Idempotency-Key": "Too long"})

        booking = BookingConfirmService.confirm(
            user=request.user,
            lesson_id=lesson_id,
            slot_id=slot_id,
            idempotency_key=idempotency_key,
        )

        return Response(
            {
                "booking_id": str(booking.id),
                "lesson_id": booking.lesson_id,
                "slot_id": booking.slot_id,
                "status": booking.status,
            },
            status=status.HTTP_200_OK,
        )


class CancelBookingView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "confirm"

    @extend_schema(
        tags=["Bookings"],
        summary="Cancel booking",
        responses={200: None, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
    )
    def post(self, request, booking_id):
        booking = BookingCancelService.cancel(
            booking_id=booking_id,
            user=request.user
        )
        return Response(
            {
                "booking_id": str(booking.id),
                "status": booking.status,
            },
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Bookings"],
    summary="List my bookings",
    parameters=[
        OpenApiParameter("status", str, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("date_from", str, OpenApiParameter.QUERY, required=False, description="YYYY-MM-DD"),
        OpenApiParameter("date_to", str, OpenApiParameter.QUERY, required=False, description="YYYY-MM-DD"),
        OpenApiParameter("lesson_id", int, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("ordering", str, OpenApiParameter.QUERY, required=False, description="created_at|starts_at with optional '-'"),
        OpenApiParameter("limit", int, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("offset", int, OpenApiParameter.QUERY, required=False),
    ],
)
class MyBookingsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    filterset_class = BookingFilter
    ordering_fields = ["created_at", "starts_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        if self.request.user.role not in ("user", "admin"):
            raise PermissionDenied("Only students can view their bookings here.")

        return (
            Booking.objects
            .filter(user=self.request.user)
            .select_related("lesson")
            .order_by("-created_at")
        )


@extend_schema(tags=["Bookings"], summary="List bookings for teacher")
class TeacherBookingsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    filterset_class = BookingFilter
    ordering_fields = ["created_at", "starts_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
    
        if self.request.user.role not in ("teacher", "admin"):
            raise PermissionDenied("Only teachers can view teacher bookings.")

        qs = Booking.objects.select_related("lesson").order_by("-created_at")

        if self.request.user.role == "teacher":
            qs = qs.filter(lesson__teacher=self.request.user)

        return qs


@extend_schema(
    tags=["Bookings"],
    summary="List bookings (admin)",
    parameters=[
        OpenApiParameter("status", str, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("date_from", str, OpenApiParameter.QUERY, required=False, description="YYYY-MM-DD"),
        OpenApiParameter("date_to", str, OpenApiParameter.QUERY, required=False, description="YYYY-MM-DD"),
        OpenApiParameter("lesson_id", int, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("user_id", int, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("teacher_id", int, OpenApiParameter.QUERY, required=False),
        OpenApiParameter(
            "ordering",
            str,
            OpenApiParameter.QUERY,
            required=False,
            description="created_at|starts_at with optional '-'",
        ),
        OpenApiParameter("limit", int, OpenApiParameter.QUERY, required=False),
        OpenApiParameter("offset", int, OpenApiParameter.QUERY, required=False),
    ],
    responses={200: BookingListSerializer, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer},
)
class AdminBookingsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    filterset_class = BookingFilter
    ordering_fields = ["created_at", "starts_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()

        if self.request.user.role != "admin":
            raise PermissionDenied("Admin only.")

        return Booking.objects.select_related("lesson").order_by("-created_at")