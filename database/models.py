import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.connection import Base


class TableModel(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String(20), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    zone = Column(String(50), nullable=False, default="main-hall")
    is_active = Column(Boolean, default=True, nullable=False)

    # Bi-directional relationship
    reservations = relationship(
        "ReservationModel", 
        back_populates="table", 
        cascade="all, delete-orphan"
    )


class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(30), nullable=False)
    party_size = Column(Integer, nullable=False)
    
    reservation_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(
        DateTime, 
        default=lambda: datetime.datetime.now(datetime.timezone.utc), 
        nullable=False
    )
    
    # Indexed foreign key for fast table-overlap queries
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False, index=True)
    
    # Relationship
    table = relationship("TableModel", back_populates="reservations")