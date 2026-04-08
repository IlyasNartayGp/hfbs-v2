from django.urls import path
from .service_views import GenerateTicketView, DownloadTicketView

urlpatterns = [
    path("generate/", GenerateTicketView.as_view()),
    path("<str:booking_id>/", DownloadTicketView.as_view()),
    path("<str:booking_id>/download/", DownloadTicketView.as_view()),
]
