import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.connection import Base

class TableModel(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String, unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    # Bi-directional relationship
    reservations = relationship("ReservationModel", back_populates="table", cascade="all, delete-orphan")


class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    party_size = Column(Integer, nullable=False)
    reservation_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    table = relationship("TableModel", back_populates="reservations")