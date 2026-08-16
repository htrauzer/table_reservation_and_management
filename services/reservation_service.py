import datetime
from datetime import timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import TableModel, ReservationModel
from api.schemas import TableCreate, ReservationCreate
from errors.handlers import (
    TableConflictException, 
    TableNotFoundException, 
    TableCapacityException,
    RestaurantException
)

class ReservationService:
    @staticmethod
    def get_table_by_id(db: Session, table_id: int) -> TableModel:
        table = db.query(TableModel).filter(TableModel.id == table_id).first()
        if not table:
            raise TableNotFoundException()
        return table

    @staticmethod
    def create_table(db: Session, table_data: TableCreate) -> TableModel:
        existing = db.query(TableModel).filter(TableModel.table_number == table_data.table_number).first()
        if existing:
            raise RestaurantException(f"Table '{table_data.table_number}' already exists.")
        
        db_table = TableModel(**table_data.model_dump())
        db.add(db_table)
        db.commit()
        db.refresh(db_table)
        return db_table

    @staticmethod
    def list_all_tables(db: Session, skip: int = 0, limit: int = 100) -> List[TableModel]:
        return db.query(TableModel).offset(skip).limit(limit).all()

    @staticmethod
    def is_table_available(db: Session, table_id: int, r_time: datetime.datetime, buffer_hours: int = 2) -> bool:
        """
        Check logic to see if a table has an overlapping booking within reservation buffers.
        """
        start_buffer = r_time - datetime.timedelta(hours=buffer_hours)
        end_buffer = r_time + datetime.timedelta(hours=buffer_hours)

        overlapping = db.query(ReservationModel).filter(
            ReservationModel.table_id == table_id,
            ReservationModel.reservation_time > start_buffer,
            ReservationModel.reservation_time < end_buffer
        ).first()

        return overlapping is None

    @classmethod
    def create_reservation(cls, db: Session, r_data: ReservationCreate) -> ReservationModel:
        # 1. Fetch table and validate existence and activity status
        table = cls.get_table_by_id(db, r_data.table_id)
        if not table.is_active:
            raise RestaurantException("The selected table is currently out of service.")

        # 2. Check Capacity limits
        if r_data.party_size > table.capacity:
            raise TableCapacityException(f"This table holds a maximum of {table.capacity} guests.")

        # 3. Prevent past bookings
        if r_data.reservation_time < datetime.datetime.utcnow():
            raise RestaurantException("Reservations cannot be made for past dates or times.")

        # 4. Enforce Operating Hours: 10:00 to 00:00 (Hour must be between 10 and 23 inclusive)
        booking_hour = r_data.reservation_time.hour
        if booking_hour < 10:
            raise RestaurantException(
                "Operating hours are from 10:00 to 00:00. Please select a valid dining slot."
            )

        # 5. Check time conflict window
        if not cls.is_table_available(db, r_data.table_id, r_data.reservation_time):
            raise TableConflictException()

        # 6. Save the reservation
        db_reservation = ReservationModel(**r_data.model_dump())
        db.add(db_reservation)
        db.commit()
        db.refresh(db_reservation)
        return db_reservation

    @staticmethod
    def list_all_reservations(db: Session, skip: int = 0, limit: int = 100) -> List[ReservationModel]:
        return db.query(ReservationModel).offset(skip).limit(limit).all()