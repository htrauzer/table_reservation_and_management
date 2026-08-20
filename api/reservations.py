from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from api.schemas import ReservationCreate, ReservationResponse
from services.reservation_service import ReservationService

router = APIRouter(prefix="/reservations", tags=["Guest Reservations"])


@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new reservation"
)
def book_a_table(
    reservation: ReservationCreate,
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """
    Submit a booking request. Validates table capacity, open status,
    and checks for temporal time conflicts automatically.
    """
    return service.create_reservation(db, reservation)


@router.get(
    "/",
    response_model=List[ReservationResponse],
    summary="List all reservations"
)
def get_all_bookings(
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """Fetch all reservations (Admin view / schedule monitoring)."""
    return service.list_all_reservations(db, skip=skip, limit=limit)


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Get single reservation details"
)
def get_booking_by_id(
    reservation_id: int,
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """Fetch details for a specific reservation by its unique ID."""
    booking = service.get_reservation_by_id(db, reservation_id=reservation_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {reservation_id} does not exist"
        )
    return booking


@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a reservation"
)
def cancel_booking(
    reservation_id: int,
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """Cancel/delete an existing reservation."""
    deleted = service.delete_reservation(db, reservation_id=reservation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {reservation_id} does not exist"
        )
    return None