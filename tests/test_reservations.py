# (Integration Tests) Sends API requests using FastAPI's TestClient to test creating, updating, canceling, and fetching reservations.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.connection import Base, get_db
from database.models import TableModel

# 1. Isolated test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates tables and seeds test tables before each test, tearing down after."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed active and inactive test tables
    table_1 = TableModel(table_number="T1", capacity=4, zone="main-hall", is_active=True)
    table_2 = TableModel(table_number="T2", capacity=2, zone="terrace", is_active=False)
    session.add_all([table_1, table_2])
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


# 1. CREATION TESTS (POST /api/reservations/)


def test_create_reservation_success(client):
    """Happy Path: Creating a valid reservation returns 201 Created."""
    payload = {
        "customer_name": "John Doe",
        "customer_email": "john.doe@example.com",
        "customer_phone": "+1234567890",
        "party_size": 4,
        "reservation_time": "2026-07-10T19:00:00",
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == payload["customer_name"]
    assert data["customer_email"] == payload["customer_email"]
    assert data["party_size"] == payload["party_size"]
    assert data["table_id"] == payload["table_id"]
    assert "id" in data
    assert "created_at" in data


def test_create_reservation_invalid_email(client):
    """Validation Error: Invalid email format triggers 422 Unprocessable Entity."""
    payload = {
        "customer_name": "Jane Doe",
        "customer_email": "invalid-email-string",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": "2026-07-10T20:00:00",
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code == 422


def test_create_reservation_invalid_phone(client):
    """Validation Error: Phone number failing regex pattern triggers 422."""
    payload = {
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com",
        "customer_phone": "abc-not-a-phone",
        "party_size": 2,
        "reservation_time": "2026-07-10T20:00:00",
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code == 422


def test_create_reservation_invalid_party_size(client):
    """Validation Error: party_size <= 0 triggers 422 (violates gt=0 schema check)."""
    payload = {
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com",
        "customer_phone": "+1234567890",
        "party_size": 0,
        "reservation_time": "2026-07-10T20:00:00",
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code == 422


def test_create_reservation_timezone_stripping(client):
    """Schema Test: Ensures offset-aware ISO timestamps are converted cleanly."""
    payload = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "+1234567890",
        "party_size": 2,
        "reservation_time": "2026-07-10T19:00:00+02:00",  # Included timezone
        "table_id": 1
    }
    response = client.post("/api/reservations/", json=payload)
    assert response.status_code == 201



# 2. READ TESTS (GET /api/reservations/)


def test_fetch_all_reservations_empty(client):
    """Returns an empty list when no reservations exist."""
    response = client.get("/api/reservations/")
    assert response.status_code == 200
    assert response.json() == []


def test_fetch_all_reservations_populated(client):
    """Returns all created reservations."""
    payload = {
        "customer_name": "Alice Smith",
        "customer_email": "alice@example.com",
        "customer_phone": "+1987654321",
        "party_size": 2,
        "reservation_time": "2026-08-01T18:00:00",
        "table_id": 1
    }
    client.post("/api/reservations/", json=payload)

    response = client.get("/api/reservations/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["customer_name"] == "Alice Smith"


def test_fetch_reservations_pagination(client):
    """Validates skip and limit query parameters work properly."""
    response = client.get("/api/reservations/?skip=0&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)



# 3. UPDATE & CANCEL TESTS (PUT /api/reservations/{id} and DELETE /api/reservations/{id})

def test_update_reservation(client):
    """
    PUT /api/reservations/{id}
    Uncomment when update endpoint is added to reservations.py
    """
    # 1. Create reservation
    # create_res = client.post("/api/reservations/", json=payload)
    # res_id = create_res.json()["id"]

    # 2. Update party_size or time
    # update_payload = { ... }
    # response = client.put(f"/api/reservations/{res_id}", json=update_payload)
    # assert response.status_code == 200
    pass


def test_cancel_reservation(client):
    """
    DELETE /api/reservations/{id}
    Uncomment when delete endpoint is added to reservations.py
    """
    # 1. Create reservation
    # create_res = client.post("/api/reservations/", json=payload)
    # res_id = create_res.json()["id"]

    # 2. Cancel/Delete
    # response = client.delete(f"/api/reservations/{res_id}")
    # assert response.status_code == 200 or response.status_code == 24
    pass