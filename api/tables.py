from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database.connection import get_db
from api.schemas import TableCreate, TableResponse
from services.reservation_service import ReservationService

router = APIRouter(prefix="/tables", tags=["Restaurant Tables Management"])

@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def add_new_table(table: TableCreate, db: Session = Depends(get_db)):
    """Add a new physical dining table to the floor plan."""
    return ReservationService.create_table(db, table)

@router.get("/", response_model=List[TableResponse])
def get_floor_plan(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch all dining tables registered in the system."""
    return ReservationService.list_all_tables(db, skip=skip, limit=limit)