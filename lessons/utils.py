from datetime import timedelta
from django.utils import timezone
from .models import LessonSlot
from django_redis import get_redis_connection

def generate_slots_for_lesson(lesson, start_time, count=3):
    slots = []
    for i in range(count):
        slot_start = start_time + timedelta(minutes=i * lesson.duration)
        slot_end = slot_start + timedelta(minutes=lesson.duration)
        slot = LessonSlot(
            lesson=lesson,
            starts_at=slot_start,
            ends_at=slot_end
        )
        slots.append(slot)
    LessonSlot.objects.bulk_create(slots)
    

def invalidate_lesson_cache(lesson_id):
    redis = get_redis_connection("default")
    pattern = f"avail:{lesson_id}:*"

    for key in redis.scan_iter(pattern):
        redis.delete(key)