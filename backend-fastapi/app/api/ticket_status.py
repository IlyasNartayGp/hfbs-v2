import os

from fastapi import APIRouter, HTTPException, Response


router = APIRouter()


@router.head("/api/bookings/{booking_id}/ticket", include_in_schema=False)
@router.head("/api/bookings/{booking_id}/ticket/", include_in_schema=False)
async def ticket_ready_status(booking_id: str):
    path = f"/app/media/tickets/{booking_id}.pdf"
    if os.path.exists(path):
        return Response(status_code=200)
    raise HTTPException(status_code=404, detail="Ticket is still being generated")
