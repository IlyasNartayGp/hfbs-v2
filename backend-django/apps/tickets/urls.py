from django.urls import path
from .views import GenerateTicketView, DownloadTicketView

urlpatterns = [
    path("generate/", GenerateTicketView.as_view()),
    path("<str:booking_id>/download/", DownloadTicketView.as_view()),
]
