from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database.connection import get_db
from api.schemas import ReservationCreate, ReservationResponse
from services.reservation_service import ReservationService

router = APIRouter(prefix="/reservations", tags=["Guest Reservations"])

@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def book_a_table(reservation: ReservationCreate, db: Session = Depends(get_db)):
    """
    Submit a booking request. Validates table capacity, open status,
    and checks for temporal time conflicts automatically.
    """
    return ReservationService.create_reservation(db, reservation)

@router.get("/", response_model=List[ReservationResponse])
def get_all_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch all reservations (Admin view / schedule monitoring)."""
    return ReservationService.list_all_reservations(db, skip=skip, limit=limit)