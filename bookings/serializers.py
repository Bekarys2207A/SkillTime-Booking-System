from rest_framework import serializers

class ConfirmBookingSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    slot_id = serializers.IntegerField()


class BookingResponseSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    lesson_id = serializers.IntegerField()
    slot_id = serializers.IntegerField()
    status = serializers.CharField()