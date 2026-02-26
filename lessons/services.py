from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django_redis import get_redis_connection
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import LessonSlot


class AvailabilityService:
    CACHE_TTL = 60

    @staticmethod
    def _cleanup_expired_holds(lesson_id: int):
        LessonSlot.objects.filter(
            lesson_id=lesson_id,
            status=LessonSlot.STATUS_HELD,
            held_until__isnull=False,
            held_until__lte=timezone.now(),
        ).update(
            status=LessonSlot.STATUS_AVAILABLE,
            held_by=None,
            held_until=None,
        )

    @staticmethod
    def get_availability(lesson_id: int, date_str: str):
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        AvailabilityService._cleanup_expired_holds(lesson_id)

        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)

        cache_key = f"avail:{lesson_id}:{date_str}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        slots = LessonSlot.objects.filter(
            lesson_id=lesson_id,
            starts_at__gte=start_of_day,
            starts_at__lt=end_of_day,
            status=LessonSlot.STATUS_AVAILABLE,
        ).order_by("starts_at")

        result = [
            {"id": slot.id, "starts_at": slot.starts_at.isoformat(), "ends_at": slot.ends_at.isoformat()}
            for slot in slots
        ]

        cache.set(cache_key, result, timeout=AvailabilityService.CACHE_TTL)
        return result


class SlotHoldService:
    HOLD_TTL_SECONDS = 5 * 60      
    LOCK_TTL_SECONDS = 10          

    @staticmethod
    def hold_slot(*, user, lesson_id: int, slot_id: int) -> LessonSlot:
        redis = get_redis_connection("default")
        lock_key = f"lock:slot:{slot_id}"

        lock = redis.lock(
            lock_key,
            timeout=SlotHoldService.LOCK_TTL_SECONDS,
            blocking_timeout=2,
        )

        acquired = lock.acquire(blocking=True)
        if not acquired:
            raise ValidationError({"detail": "Slot is busy, try again."})

        try:
            with transaction.atomic():
                slot = get_object_or_404(
                    LessonSlot.objects.select_for_update(),
                    id=slot_id,
                    lesson_id=lesson_id
                )

                if slot.status == LessonSlot.STATUS_BOOKED:
                    raise ValidationError({"detail": "Slot already booked."})

                if slot.status == LessonSlot.STATUS_HELD and not slot.is_hold_expired():
                    if slot.held_by_id != user.id:
                        raise ValidationError({"detail": "Slot is held by another user."})

                if slot.status == LessonSlot.STATUS_HELD and slot.is_hold_expired():
                    slot.status = LessonSlot.STATUS_AVAILABLE
                    slot.held_by = None
                    slot.held_until = None

                slot.status = LessonSlot.STATUS_HELD
                slot.held_by = user
                slot.held_until = timezone.now() + timedelta(seconds=SlotHoldService.HOLD_TTL_SECONDS)
                slot.save(update_fields=["status", "held_by", "held_until"])

                return slot

        finally:
            try:
                lock.release()
            except Exception:
                pass