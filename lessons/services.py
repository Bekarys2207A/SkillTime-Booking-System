from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone
from django.core.cache import cache
from .models import LessonSlot


class AvailabilityService:
    CACHE_TTL = 60

    @staticmethod
    def get_availability(lesson_id: int, date_str: str):
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        
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
            {
                "starts_at": slot.starts_at.isoformat(),
                "ends_at": slot.ends_at.isoformat(),
            }
            for slot in slots
        ]

        cache.set(cache_key, result, timeout=AvailabilityService.CACHE_TTL)
        return result