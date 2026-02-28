from django.urls import path
from .views import ConfirmBookingView, CancelBookingView

urlpatterns = [
    path("confirm/", ConfirmBookingView.as_view(), name="booking-confirm"),
    path("<uuid:booking_id>/cancel/", CancelBookingView.as_view(), name="booking-cancel"),
]