import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# --- Table Schemas ---
class TableBase(BaseModel):
    table_number: str = Field(..., min_length=1, max_length=10, json_schema_extra={"example": "T1"})
    capacity: int = Field(..., gt=0, json_schema_extra={"example": 4})
    zone: str = Field(default="main-hall", json_schema_extra={"example": "main-hall"})
    is_active: Optional[bool] = True

class TableCreate(TableBase):
    pass

class TableResponse(TableBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Reservation Schemas ---
class ReservationBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "John Doe"})
    customer_email: EmailStr = Field(..., json_schema_extra={"example": "john.doe@example.com"})
    customer_phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$", json_schema_extra={"example": "+1234567890"})
    party_size: int = Field(..., gt=0, json_schema_extra={"example": 4})
    reservation_time: datetime.datetime = Field(..., json_schema_extra={"example": "2026-07-10T19:00:00"})

class ReservationCreate(ReservationBase):
    table_id: int = Field(..., description="ID of the table to reserve")

class ReservationResponse(ReservationBase):
    id: int
    created_at: datetime.datetime
    table: TableResponse
    model_config = ConfigDict(from_attributes=True)