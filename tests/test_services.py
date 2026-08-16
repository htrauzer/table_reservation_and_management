# (Unit Tests) Tests internal calculation logic in isolation (e.g., checking if party size fits table capacity, double-booking time overlap logic, or operating hours validation) without triggering web requests.

import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from database.models import TableModel, ReservationModel
from api.schemas import TableCreate, ReservationCreate
from services.reservation_service import ReservationService
from errors.handlers import (
    TableConflictException,
    TableNotFoundException,
    TableCapacityException,
    RestaurantException,
)


# ==============================================================================
# TABLE SERVICE TESTS
# ==============================================================================

def test_create_table_success(db_session: Session):
    """Test creating a new table successfully."""
    table_in = TableCreate(table_number="T10", capacity=4, is_active=True)
    created_table = ReservationService.create_table(db_session, table_in)

    assert created_table.id is not None
    assert created_table.table_number == "T10"
    assert created_table.capacity == 4
    assert created_table.is_active is True


def test_create_table_duplicate_number_raises_exception(db_session: Session):
    """Test that creating a table with a duplicate table_number raises RestaurantException."""
    table_in = TableCreate(table_number="T1", capacity=2, is_active=True)
    # The first creation works
    ReservationService.create_table(db_session, table_in)
    
    # Attempt to create duplicate (notice the fix to use db_session and table_in)
    with pytest.raises(RestaurantException) as exc_info:
        ReservationService.create_table(db_session, table_in)

    assert "already exists" in str(exc_info.value.detail)


def test_get_table_by_id_success(db_session: Session):
    """Test retrieving an existing table by ID."""
    table_in = TableCreate(table_number="T2", capacity=4, is_active=True)
    created = ReservationService.create_table(db_session, table_in)

    fetched = ReservationService.get_table_by_id(db_session, created.id)
    assert fetched.id == created.id
    assert fetched.table_number == "T2"


def test_get_table_by_id_not_found_raises_exception(db_session: Session):
    """Test that fetching a non-existent table ID raises TableNotFoundException."""
    with pytest.raises(TableNotFoundException):
        ReservationService.get_table_by_id(db_session, table_id=9999)


# ==============================================================================
# RESERVATION SERVICE TESTS
# ==============================================================================

def test_create_reservation_success(db_session: Session):
    """Test successful creation of a reservation when all rules are met."""
    # 1. Setup active table
    table = ReservationService.create_table(
        db_session, TableCreate(table_number="T1", capacity=4, is_active=True)
    )

    # 2. Setup future booking time within operating hours (e.g., tomorrow at 14:00 UTC)
    future_time = datetime.now(timezone.utc) + timedelta(days=1)
    future_time = future_time.replace(hour=14, minute=0, second=0, microsecond=0)

    res_in = ReservationCreate(
        customer_name="Alice Smith",
        customer_email="alice@example.com",
        customer_phone="+123456789",
        party_size=4,
        reservation_time=future_time,
        table_id=table.id,
    )

    created_res = ReservationService.create_reservation(db_session, res_in)

    assert created_res.id is not None
    assert created_res.customer_name == "Alice Smith"
    assert created_res.table_id == table.id


def test_create_reservation_inactive_table_raises_exception(db_session: Session):
    """Test that reserving an inactive table raises RestaurantException."""
    table = ReservationService.create_table(
        db_session, TableCreate(table_number="T-INACTIVE", capacity=4, is_active=False)
    )

    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=12, minute=0)

    res_in = ReservationCreate(
        customer_name="Bob",
        customer_email="bob@example.com",
        customer_phone="+123456789",
        party_size=2,
        reservation_time=future_time,
        table_id=table.id,
    )

    with pytest.raises(RestaurantException) as exc_info:
        ReservationService.create_reservation(db_session, res_in)

    assert "out of service" in str(exc_info.value.detail)


def test_create_reservation_exceeds_capacity_raises_exception(db_session: Session):
    """Test that reserving for a party larger than table capacity raises TableCapacityException."""
    table = ReservationService.create_table(
        db_session, TableCreate(table_number="T-SMALL", capacity=2, is_active=True)
    )

    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=15, minute=0)

    res_in = ReservationCreate(
        customer_name="Group of 6",
        customer_email="group@example.com",
        customer_phone="+123456789",
        party_size=6,
        reservation_time=future_time,
        table_id=table.id,
    )

    with pytest.raises(TableCapacityException):
        ReservationService.create_reservation(db_session, res_in)


def test_create_reservation_past_date_raises_exception(db_session: Session):
    """Test that booking a time in the past raises RestaurantException."""
    table = ReservationService.create_table(
        db_session, TableCreate(table_number="T1", capacity=4, is_active=True)
    )

    past_time = datetime.now(timezone.utc) - timedelta(days=1)

    res_in = ReservationCreate(
        customer_name="Time Traveler",
        customer_email="past@example.com",
        customer_phone="+123456789",
        party_size=2,
        reservation_time=past_time,
        table_id=table.id,
    )

    with pytest.raises(RestaurantException) as exc_info:
        ReservationService.create_reservation(db_session, res_in)

    assert "past dates" in str(exc_info.value.detail)


def test_create_reservation_outside_operating_hours_raises_exception(db_session: Session):
    """Test that booking outside 10:00-23:59 (e.g., at 08:00 AM) raises RestaurantException."""
    table = ReservationService.create_table(
        db_session, TableCreate(table_number="T1", capacity=4, is_active=True)
    )

    early_time = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=8, minute=0)

    res_in = ReservationCreate(
        customer_name="Early Bird",
        customer_email="early@example.com",
        customer_phone="+123456789",
        party_size=2,
        reservation_time=early_time,
        table_id=table.id,
    )

    with pytest.raises(RestaurantException) as exc_info:
        ReservationService.create_reservation(db_session, res_in)

    assert "Operating hours" in str(exc_info.value.detail)


def test_create_reservation_time_conflict_raises_exception(db_session: Session):
    """Test that overlapping reservations within 2 hours trigger TableConflictException."""
    table = ReservationService.create_table(
        db_session, TableCreate(table_number="T1", capacity=4, is_active=True)
    )

    booking_time = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)

    first_res = ReservationCreate(
        customer_name="First Guest",
        customer_email="first@example.com",
        customer_phone="+123456789",
        party_size=2,
        reservation_time=booking_time,
        table_id=table.id,
    )
    ReservationService.create_reservation(db_session, first_res)

    # Attempt to book 1 hour later (within 2-hour window)
    conflicting_time = booking_time + timedelta(hours=1)
    second_res = ReservationCreate(
        customer_name="Second Guest",
        customer_email="second@example.com",
        customer_phone="+987654321",
        party_size=2,
        reservation_time=conflicting_time,
        table_id=table.id,
    )

    with pytest.raises(TableConflictException):
        ReservationService.create_reservation(db_session, second_res)