from rest_framework import serializers
from .models import Lesson

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'teacher', 'title', 'description', 'duration', 'capacity', 'file_path', 'is_active', 'created_at']
        read_only_fields = ['id', 'teacher', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.role == 'teacher':
            validated_data['teacher'] = request.user
        return super().create(validated_data)
    

class HoldSlotSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField()