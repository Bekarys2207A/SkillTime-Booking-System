from rest_framework import serializers
from .models import Booking

class ConfirmBookingSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    slot_id = serializers.IntegerField()

class BookingListSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    teacher_id = serializers.IntegerField(source="lesson.teacher_id", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user_id",
            "lesson_id",
            "lesson_title",
            "teacher_id",
            "slot_id",
            "starts_at",
            "ends_at",
            "status",
            "created_at",
        ]
        read_only_fields = fields