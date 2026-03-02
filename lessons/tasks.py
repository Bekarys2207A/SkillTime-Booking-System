from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import LessonSlot
from .utils import invalidate_availability_cache

try:
    from audit.services import audit_log
except Exception:
    audit_log = None


@shared_task
def release_expired_holds():
    """
    Освобождает все просроченные held-слоты.
    Запускается по расписанию Celery Beat.
    """
    now = timezone.now()

    expired = (
        LessonSlot.objects
        .filter(status=LessonSlot.STATUS_HELD, held_until__isnull=False, held_until__lte=now)
        .values("id", "lesson_id", "starts_at")
    )

    expired_list = list(expired)
    if not expired_list:
        return {"released": 0}

    cache_keys = set()
    slot_ids = []
    for row in expired_list:
        slot_ids.append(row["id"])
        cache_keys.add((row["lesson_id"], row["starts_at"].date().isoformat()))

    with transaction.atomic():
        LessonSlot.objects.filter(id__in=slot_ids).update(
            status=LessonSlot.STATUS_AVAILABLE,
            held_by=None,
            held_until=None,
        )

    for lesson_id, date_str in cache_keys:
        invalidate_availability_cache(lesson_id=lesson_id, date_str=date_str)

    if audit_log:
        audit_log(
            actor=None,
            action="release_holds",
            entity="LessonSlot",
            entity_id=None,
            meta={"released": len(slot_ids)},
        )

    return {"released": len(slot_ids)}