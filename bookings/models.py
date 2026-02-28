import uuid
from django.conf import settings
from django.db import models

class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"   

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    lesson = models.ForeignKey("lessons.Lesson", on_delete=models.CASCADE, related_name="bookings")
    slot = models.ForeignKey("lessons.LessonSlot", on_delete=models.PROTECT, related_name="bookings")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),        
            models.Index(fields=["lesson", "created_at"]),      
            models.Index(fields=["status", "created_at"]),      
            models.Index(fields=["starts_at"]),                
            models.Index(fields=["slot"]),                      
        ]

    def __str__(self):
        return f"Booking {self.id} user={self.user_id} slot={self.slot_id} status={self.status}"