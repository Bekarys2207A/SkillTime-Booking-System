import uuid
from django.db import models
from django.conf import settings

# Create your models here.

class FileUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads")
    lesson = models.ForeignKey("lessons.Lesson", on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="lesson_files/")
    size_bytes = models.PositiveIntegerField()
    mime = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["lesson"]),
            models.Index(fields=["owner"]),
        ]

    def __str__(self):
        return f"{self.file.name} ({self.mime})"