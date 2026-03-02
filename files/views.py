from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404

from lessons.models import Lesson
from .services import FileUploadService

from audit.services import AuditService
from audit.models import AuditLog


class LessonFileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)

        if request.user.role not in ("teacher", "admin"):
            raise PermissionDenied("Only teacher or admin can upload files.")

        if request.user.role == "teacher" and lesson.teacher_id != request.user.id:
            raise PermissionDenied("You cannot upload to another teacher's lesson.")

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError({"file": "File is required."})

        file_obj = FileUploadService.create(
            owner=request.user,
            lesson=lesson,
            uploaded_file=uploaded_file,
        )

        AuditService.log(
            actor=request.user,
            action=AuditLog.ACTION_FILE_UPLOAD,
            entity="FileUpload",
            entity_id=file_obj.id,
            meta={
                "lesson_id": lesson.id,
                "mime": file_obj.mime,
                "size_bytes": file_obj.size_bytes,
                "path": file_obj.file.name,
            },
        )

        return Response({
            "file_id": str(file_obj.id),
            "lesson_id": lesson.id,
            "file_url": file_obj.file.url,
            "mime": file_obj.mime,
            "size_bytes": file_obj.size_bytes,
        })