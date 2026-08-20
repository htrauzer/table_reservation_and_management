from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


# --- Table Schemas ---

class TableBase(BaseModel):
    """Shared properties for dining tables."""
    table_number: str = Field(..., min_length=1, max_length=10, json_schema_extra={"example": "T1"})
    capacity: int = Field(..., gt=0, le=50, json_schema_extra={"example": 4})
    zone: str = Field(default="main-hall", max_length=50, json_schema_extra={"example": "main-hall"})
    is_active: bool = True


class TableCreate(TableBase):
    """Schema for admin table creation."""
    pass


class TableResponse(TableBase):
    """Schema for table read operations."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


# --- Reservation Schemas ---

class ReservationBase(BaseModel):
    """Base reservation attributes."""
    customer_name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "John Doe"})
    customer_email: EmailStr = Field(..., json_schema_extra={"example": "john.doe@example.com"})
    customer_phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$", json_schema_extra={"example": "+1234567890"})
    party_size: int = Field(..., gt=0, le=50, json_schema_extra={"example": 4})
    reservation_time: datetime = Field(..., json_schema_extra={"example": "2026-09-15T19:00:00"})

    @field_validator("reservation_time")
    @classmethod
    def validate_and_make_naive(cls, v: datetime) -> datetime:
        """Strips timezone info and verifies the reservation date is in the future."""
        # Convert to naive UTC/local time for consistency
        naive_dt = v.replace(tzinfo=None) if v.tzinfo is not None else v
        
        # Guard clause against past reservations
        if naive_dt < datetime.now().replace(microsecond=0):
            raise ValueError("Reservation time must be in the future")
            
        return naive_dt


class ReservationCreate(ReservationBase):
    """Schema used when submitting a new booking request."""
    table_id: int = Field(..., gt=0, description="ID of the table to reserve", json_schema_extra={"example": 1})


class ReservationResponse(ReservationBase):
    """Schema returned to client upon successful booking or query."""
    id: int
    table_id: int
    created_at: datetime
    table: TableResponse
    
    model_config = ConfigDict(from_attributes=True)