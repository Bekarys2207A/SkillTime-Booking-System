from datetime import timedelta
from django_redis import get_redis_connection
from .models import LessonSlot
from .cache_keys import lessons_list_key, lesson_detail_key


def generate_slots_for_lesson(lesson, start_time, count=3):
    slots = []
    for i in range(count):
        slot_start = start_time + timedelta(minutes=i * lesson.duration)
        slot_end = slot_start + timedelta(minutes=lesson.duration)
        slots.append(
            LessonSlot(
                lesson=lesson,
                starts_at=slot_start,
                ends_at=slot_end,
            )
        )
    LessonSlot.objects.bulk_create(slots)


def invalidate_lesson_cache(lesson_id: int):
    redis = get_redis_connection("default")
    redis.delete(lesson_detail_key(lesson_id))
    redis.delete(lessons_list_key())
    pattern = f"avail:{lesson_id}:*"
    for key in redis.scan_iter(match=pattern):
        redis.delete(key)


def invalidate_availability_cache(*, lesson_id: int, date_str: str):
    redis = get_redis_connection("default")
    redis.delete(f"avail:{lesson_id}:{date_str}")