from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from api.schemas import TableCreate, TableResponse
from services.reservation_service import ReservationService

router = APIRouter(prefix="/tables", tags=["Restaurant Tables Management"])


@router.post(
    "/",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new dining table"
)
def add_new_table(
    table: TableCreate,
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """Add a new physical dining table to the floor plan."""
    return service.create_table(db, table)


@router.get(
    "/",
    response_model=List[TableResponse],
    summary="List floor plan tables"
)
def get_floor_plan(
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=100, description="Max tables to return"),
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """Fetch all dining tables registered in the system."""
    return service.list_all_tables(db, skip=skip, limit=limit)


@router.get(
    "/{table_id}",
    response_model=TableResponse,
    summary="Get single table details"
)
def get_table_by_id(
    table_id: int,
    db: Session = Depends(get_db),
    service: ReservationService = Depends()
):
    """Fetch details and availability status for a specific dining table."""
    table = service.get_table_by_id(db, table_id=table_id)
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID {table_id} does not exist"
        )
    return table