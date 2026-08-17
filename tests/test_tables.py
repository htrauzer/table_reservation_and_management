# (Integration Tests) Tests CRUD operations on restaurant tables (adding a table, marking status as reserved/occupied, listing available tables).

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.connection import Base, get_db
from database.models import TableModel, ReservationModel

# 1. Setup isolated in-memory SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates tables and seeds initial test tables before each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Seed initial test tables
    t1 = TableModel(table_number="T1", capacity=4, zone="main-hall", is_active=True)
    t2 = TableModel(table_number="T2", capacity=2, zone="terrace", is_active=False)  # Inactive table
    session.add_all([t1, t2])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden database dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =====================================================================
# 1. TABLE MANAGEMENT TESTS (/api/tables/)
# =====================================================================

def test_create_table_success(client):
    """POST /api/tables/ - Successfully create a new table."""
    payload = {
        "table_number": "T100",
        "capacity": 6,
        "zone": "vip-room",
        "is_active": True
    }
    response = client.post("/api/tables/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["table_number"] == "T100"
    assert data["capacity"] == 6
    assert data["zone"] == "vip-room"


def test_create_table_duplicate_number_fails(client):
    """POST /api/tables/ - Creating a table with an existing table_number raises exception."""
    payload = {
        "table_number": "T1",  # T1 was seeded in fixture
        "capacity": 4,
        "zone": "main-hall"
    }
    response = client.post("/api/tables/", json=payload)
    assert response.status_code in (400, 409, 500)


def test_list_all_tables(client):
    """GET /api/tables/ - Fetch floor plan returns all registered tables."""
    response = client.get("/api/tables/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


# =====================================================================
# 2. RESERVATION SUCCESS TESTS (/api/reservations/)
# =====================================================================

def test_create_reservation_success(client):
    """POST /api/reservations/ - Happy path booking during valid operating hours."""
    future_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=18, minute=0, second=0)
    
    payload = {
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com",
        "customer_phone": "+1234567890",
        "party_size": 4,
        "reservation_time": future_time.isoformat(),
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Jane Doe"
    assert data["table_id"] == 1


def test_list_all_reservations(client):
    """GET /api/reservations/ - Fetch list of reservations."""
    future_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=19, minute=0, second=0)
    payload = {
        "customer_name": "Alice Smith",
        "customer_email": "alice@example.com",
        "customer_phone": "+1987654321",
        "party_size": 2,
        "reservation_time": future_time.isoformat(),
        "table_id": 1
    }
    client.post("/api/reservations/", json=payload)

    response = client.get("/api/reservations/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["customer_name"] == "Alice Smith"


# =====================================================================
# 3. RESERVATION BUSINESS LOGIC & RULE TESTS
# =====================================================================

def test_create_reservation_nonexistent_table(client):
    """Rule 1: Booking a table_id that doesn't exist raises TableNotFoundException."""
    future_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=18, minute=0)
    payload = {
        "customer_name": "Ghost User",
        "customer_email": "ghost@example.com",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": future_time.isoformat(),
        "table_id": 9999
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code in (400, 404)


def test_create_reservation_inactive_table(client):
    """Rule 1: Booking an out-of-service/inactive table fails."""
    future_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=18, minute=0)
    payload = {
        "customer_name": "Out of Service Booking",
        "customer_email": "test@example.com",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": future_time.isoformat(),
        "table_id": 2  # Table 2 is inactive (is_active=False)
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code in (400, 422)


def test_create_reservation_exceeds_capacity(client):
    """Rule 2: Booking with party_size > table.capacity raises TableCapacityException."""
    future_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=18, minute=0)
    payload = {
        "customer_name": "Large Group",
        "customer_email": "large@example.com",
        "customer_phone": "+1234567890",
        "party_size": 8,  # Table 1 capacity is 4
        "reservation_time": future_time.isoformat(),
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code in (400, 422)


def test_create_reservation_past_date_fails(client):
    """Rule 3: Booking in the past raises exception."""
    past_time = datetime.utcnow() - timedelta(days=1)
    payload = {
        "customer_name": "Time Traveler",
        "customer_email": "traveler@example.com",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": past_time.isoformat(),
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code in (400, 422)


def test_create_reservation_outside_operating_hours(client):
    """Rule 4: Booking before 10:00 (e.g. 08:00 AM) fails operating hours check."""
    early_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=8, minute=0, second=0)
    payload = {
        "customer_name": "Early Bird",
        "customer_email": "early@example.com",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": early_time.isoformat(),
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code in (400, 422)


def test_create_reservation_buffer_conflict(client):
    """Rule 5: Booking within 2 hours of an existing reservation triggers TableConflictException."""
    base_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=18, minute=0, second=0)

    # 1. Initial reservation at 18:00
    first_payload = {
        "customer_name": "First Guest",
        "customer_email": "first@example.com",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": base_time.isoformat(),
        "table_id": 1
    }
    res1 = client.post("/api/reservations/", json=first_payload)
    assert res1.status_code == 201

    # 2. Conflicting reservation at 19:00 (within 2-hour window)
    conflict_time = base_time + timedelta(hours=1)
    second_payload = {
        "customer_name": "Conflicting Guest",
        "customer_email": "second@example.com",
        "customer_phone": "+1987654321",
        "party_size": 2,
        "reservation_time": conflict_time.isoformat(),
        "table_id": 1
    }
    res2 = client.post("/api/reservations/", json=second_payload)
    assert res2.status_code in (400, 409, 422)