from django.urls import path
from .views import ConfirmBookingView

urlpatterns = [
    path("confirm/", ConfirmBookingView.as_view(), name="booking-confirm"),
]