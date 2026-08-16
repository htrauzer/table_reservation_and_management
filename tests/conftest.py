# This will hold your database fixtures, creating a fresh, isolated SQLite test database for every test run so real app data is never modified.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import your FastAPI app, Database base model, and DB dependency
from database.models import Base
import database.models  # Import models so Base metadata includes all tables
from services.reservation_service import ReservationService

# 1. Use an in-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 2. Database Fixture: Runs for each test
@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh database session for every test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# 3. FastAPI Client Fixture: Simulates API HTTP requests
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override the real get_db dependency with our test DB session
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
        
    # Clear overrides after test finishes
    app.dependency_overrides.clear()