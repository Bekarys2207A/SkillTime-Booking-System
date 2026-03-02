from rest_framework import serializers
from .models import Lesson
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