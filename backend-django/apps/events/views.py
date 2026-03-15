from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Event, Seat
from django.shortcuts import get_object_or_404


class EventListView(APIView):
    def get(self, request):
        events = Event.objects.filter(is_active=True).values(
            "id", "name", "venue", "date",
            "total_seats", "available_seats", "sale_open"
        )
        return Response(list(events))


class EventDetailView(APIView):
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk, is_active=True)
        return Response({
            "id": event.id,
            "name": event.name,
            "venue": event.venue,
            "date": event.date,
            "description": event.description,
            "total_seats": event.total_seats,
            "available_seats": event.available_seats,
            "sale_open": event.sale_open,
        })
