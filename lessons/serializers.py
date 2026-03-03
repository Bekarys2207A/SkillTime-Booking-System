from rest_framework import serializers
from .models import Lesson, LessonSlot
from files.models import FileUpload


class LessonFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ["id", "file", "mime", "size_bytes", "created_at"]


class LessonSerializer(serializers.ModelSerializer):
    files = LessonFileSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'teacher', 'title', 'description', 'duration', 'capacity', 'is_active', 'created_at', 'files']
        read_only_fields = ['id', 'teacher', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.role == 'teacher':
            validated_data['teacher'] = request.user
        return super().create(validated_data)


class HoldSlotSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField()


class AvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField(input_formats=["%Y-%m-%d"])


class LessonSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonSlot
        fields = ["id", "lesson", "starts_at", "ends_at", "status", "held_by", "held_until"]
        read_only_fields = ["id", "lesson", "status", "held_by", "held_until"]


class LessonSlotCreateSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["ends_at"] <= attrs["starts_at"]:
            raise serializers.ValidationError({"ends_at": "ends_at must be after starts_at"})
        return attrs