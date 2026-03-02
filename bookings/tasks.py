from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

from .models import Booking

try:
    from audit.services import audit_log
except Exception:
    audit_log = None


@shared_task
def archive_bookings(days_after: int = 7):
    cutoff = timezone.now() - timedelta(days=days_after)

    qs = Booking.objects.filter(
        status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_CANCELLED],
        starts_at__lt=cutoff,
    )

    ids = list(qs.values_list("id", flat=True))
    if not ids:
        return {"archived": 0}

    with transaction.atomic():
        qs.update(status=Booking.STATUS_ARCHIVED)

    if audit_log:
        audit_log(
            actor=None,
            action="archive_bookings",
            entity="Booking",
            entity_id=None,
            meta={"archived": len(ids), "older_than_days": days_after},
        )

    return {"archived": len(ids)}