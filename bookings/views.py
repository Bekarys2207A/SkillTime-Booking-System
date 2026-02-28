from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from .serializers import ConfirmBookingSerializer
from .services import BookingConfirmService, BookingCancelService

# Create your views here.

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