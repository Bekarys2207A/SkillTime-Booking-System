from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, F


class Lesson(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        limit_choices_to={"role": "teacher"},
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text="Длительность урока в минутах")
    capacity = models.PositiveIntegerField(default=1, help_text="Максимальное количество учеников в слоте")
    is_active = models.BooleanField(default=True, help_text="Если False, урок скрыт из поиска")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.teacher.email})"


class LessonSlot(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_HELD = "held"
    STATUS_BOOKED = "booked"

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_HELD, "Held"),
        (STATUS_BOOKED, "Booked"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="slots")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

    held_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="held_slots",
    )
    held_until = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["lesson", "starts_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["held_until"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["lesson", "starts_at"], name="unique_lesson_start"),
            models.CheckConstraint(condition=Q(ends_at__gt=F("starts_at")), name="check_end_after_start"),
        ]

    def is_hold_expired(self) -> bool:
        return self.held_until is not None and self.held_until <= timezone.now()

    def __str__(self):
        return f"{self.lesson.title}: {self.starts_at.isoformat()} - {self.ends_at.isoformat()} ({self.status})"