from rest_framework.exceptions import ValidationError
from .models import FileUpload


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_MIME = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "video/mp4",
]


class FileUploadService:

    @staticmethod
    def validate(uploaded_file):
        if uploaded_file.size > MAX_FILE_SIZE:
            raise ValidationError({"file": "File too large (max 10MB)."})

        if uploaded_file.content_type not in ALLOWED_MIME:
            raise ValidationError({"file": "Unsupported file type."})

    @staticmethod
    def create(*, owner, lesson, uploaded_file):
        FileUploadService.validate(uploaded_file)

        return FileUpload.objects.create(
            owner=owner,
            lesson=lesson,
            file=uploaded_file,
            size_bytes=uploaded_file.size,
            mime=uploaded_file.content_type,
        )