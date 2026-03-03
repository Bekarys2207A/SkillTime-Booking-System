import django_filters
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