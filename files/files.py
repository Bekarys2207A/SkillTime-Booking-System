from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

from .models import FileUpload

try:
    from audit.services import audit_log
except Exception:
    audit_log = None


@shared_task
def cleanup_uploads(days: int = 30):
    """
    Удаляет файлы старше N дней (и строки из БД).
    """
    cutoff = timezone.now() - timedelta(days=days)

    qs = FileUpload.objects.filter(created_at__lt=cutoff).select_related("lesson", "owner")
    ids = list(qs.values_list("id", flat=True))

    if not ids:
        return {"deleted": 0}

    with transaction.atomic():
        for obj in qs:
            if obj.file:
                obj.file.delete(save=False)
            obj.delete()

    if audit_log:
        audit_log(
            actor=None,
            action="cleanup_uploads",
            entity="FileUpload",
            entity_id=None,
            meta={"deleted": len(ids), "older_than_days": days},
        )

    return {"deleted": len(ids)}