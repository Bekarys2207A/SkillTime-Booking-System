import uuid
from django.conf import settings
from django.db import models

# Create your models here.

class AuditLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_STATUS_CHANGE = "status_change"
    ACTION_DEACTIVATE = "deactivate"

    ACTION_HOLD = "hold"
    ACTION_CONFIRM = "confirm"
    ACTION_CANCEL = "cancel"
    ACTION_FILE_UPLOAD = "file_upload"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
        (ACTION_STATUS_CHANGE, "Status change"),
        (ACTION_DEACTIVATE, "Deactivate"),
        (ACTION_HOLD, "Hold"),
        (ACTION_CONFIRM, "Confirm"),
        (ACTION_CANCEL, "Cancel"),
        (ACTION_FILE_UPLOAD, "File upload"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs")
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    entity = models.CharField(max_length=64, db_index=True)
    entity_id = models.CharField(max_length=128, db_index=True)
    meta = models.JSONField(default=dict, blank=True)
    ts = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity", "entity_id", "ts"]),
            models.Index(fields=["actor", "ts"]),
            models.Index(fields=["action", "ts"]),
        ]
        ordering = ["-ts"]

    def __str__(self):
        return f"[{self.ts}] {self.action} {self.entity}#{self.entity_id} by {self.actor_id}"