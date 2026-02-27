from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework.exceptions import ValidationError

from lessons.models import LessonSlot
from lessons.utils import invalidate_availability_cache
from .models import Booking


class BookingConfirmService:
    IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60
    LOCK_TTL_SECONDS = 10
    LOCK_BLOCKING_TIMEOUT = 2

    @staticmethod
    def _idempotency_key_storage_key(user_id: int, idem_key: str) -> str:
        return f"idem:confirm:{user_id}:{idem_key}"

    @staticmethod
    def confirm(*, user, lesson_id: int, slot_id: int, idempotency_key: str | None):
        redis = get_redis_connection("default")

        if idempotency_key:
            stored_key = BookingConfirmService._idempotency_key_storage_key(user.id, idempotency_key)
            cached_booking_id = redis.get(stored_key)
            if cached_booking_id:
                booking_id = cached_booking_id.decode("utf-8")
                booking = Booking.objects.get(id=booking_id)
                return booking

        lock_key = f"lock:slot:{slot_id}"
        lock = redis.lock(
            lock_key,
            timeout=BookingConfirmService.LOCK_TTL_SECONDS,
            blocking_timeout=BookingConfirmService.LOCK_BLOCKING_TIMEOUT,
        )

        acquired = lock.acquire(blocking=True)
        if not acquired:
            raise ValidationError({"detail": "Slot is busy, try again."})

        try:
            with transaction.atomic():
                slot = (
                    LessonSlot.objects.select_for_update()
                    .get(id=slot_id, lesson_id=lesson_id)
                )

                if slot.status != LessonSlot.STATUS_HELD:
                    raise ValidationError({"detail": "Slot is not held."})

                if slot.held_by_id != user.id:
                    raise ValidationError({"detail": "Slot is held by another user."})

                if not slot.held_until or slot.held_until <= timezone.now():
                    raise ValidationError({"detail": "Hold expired. Please hold again."})

                if Booking.objects.filter(user=user, slot_id=slot.id, status=Booking.STATUS_CONFIRMED).exists():
                    raise ValidationError({"detail": "Already booked by you."})

                booking = Booking.objects.create(
                    user=user,
                    lesson_id=lesson_id,
                    slot=slot,
                    status=Booking.STATUS_CONFIRMED,
                    idempotency_key=idempotency_key,
                )

                slot.status = LessonSlot.STATUS_BOOKED
                slot.held_by = None
                slot.held_until = None
                slot.save(update_fields=["status", "held_by", "held_until"])

                date_str = slot.starts_at.date().isoformat()
                invalidate_availability_cache(lesson_id=lesson_id, date_str=date_str)

                if idempotency_key:
                    stored_key = BookingConfirmService._idempotency_key_storage_key(user.id, idempotency_key)
                    redis.setex(stored_key, BookingConfirmService.IDEMPOTENCY_TTL_SECONDS, str(booking.id))

                return booking

        finally:
            try:
                lock.release()
            except Exception:
                pass