from django.urls import path
from .views import LessonFileUploadView

urlpatterns = [
    path("lessons/<int:lesson_id>/file/", LessonFileUploadView.as_view()),
] 