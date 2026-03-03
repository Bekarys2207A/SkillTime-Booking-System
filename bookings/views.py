from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from .models import Booking
from .serializers import ConfirmBookingSerializer, BookingListSerializer
from .services import BookingConfirmService, BookingCancelService
from .filters import BookingFilter


class ConfirmBookingView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "confirm"

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


class MyBookingsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    filterset_class = BookingFilter
    ordering_fields = ["created_at", "starts_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.request.user.role not in ("user", "admin"):
            raise PermissionDenied("Only students can view their bookings here.")

        return (
            Booking.objects
            .filter(user=self.request.user)
            .select_related("lesson")
            .order_by("-created_at")
        )


class TeacherBookingsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    filterset_class = BookingFilter
    ordering_fields = ["created_at", "starts_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.request.user.role not in ("teacher", "admin"):
            raise PermissionDenied("Only teachers can view teacher bookings.")

        qs = Booking.objects.select_related("lesson").order_by("-created_at")

        if self.request.user.role == "teacher":
            qs = qs.filter(lesson__teacher=self.request.user)

        return qs


class AdminBookingsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    filterset_class = BookingFilter
    ordering_fields = ["created_at", "starts_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.request.user.role != "admin":
            raise PermissionDenied("Admin only.")

        return Booking.objects.select_related("lesson").order_by("-created_at")