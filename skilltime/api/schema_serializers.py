from rest_framework import serializers

class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(child=serializers.JSONField(), required=False)