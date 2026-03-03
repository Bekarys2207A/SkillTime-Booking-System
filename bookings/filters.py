import django_filters
from rest_framework import serializers

from .models import Booking


class BookingFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    lesson_id = django_filters.NumberFilter(field_name="lesson_id")

    date_from = django_filters.DateFilter(field_name="starts_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="starts_at", lookup_expr="date__lte")

    user_id = django_filters.NumberFilter(field_name="user_id")
    teacher_id = django_filters.NumberFilter(field_name="lesson__teacher_id")

    class Meta:
        model = Booking
        fields = ["status", "lesson_id", "date_from", "date_to", "user_id", "teacher_id"]


class BookingFilterSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    lesson_id = serializers.IntegerField(required=False)
    user_id = serializers.IntegerField(required=False)
    teacher_id = serializers.IntegerField(required=False)

    ordering = serializers.CharField(required=False)
    limit = serializers.IntegerField(required=False)
    offset = serializers.IntegerField(required=False)