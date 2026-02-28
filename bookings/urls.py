from django.urls import path
from .views import ConfirmBookingView, CancelBookingView, MyBookingsListView, TeacherBookingsListView, AdminBookingsListView

urlpatterns = [
    path("confirm/", ConfirmBookingView.as_view(), name="booking-confirm"),
    path("<uuid:booking_id>/cancel/", CancelBookingView.as_view(), name="booking-cancel"),
    path("me/", MyBookingsListView.as_view(), name="booking-me"),
    path("teacher/", TeacherBookingsListView.as_view(), name="booking-teacher"),
    path("admin/", AdminBookingsListView.as_view(), name="booking-admin"),
]