import uuid, enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (String, Text, Integer, Numeric, Boolean, Date, DateTime, ForeignKey,
                        CheckConstraint, Computed, func, text, Index)
from sqlalchemy.dialects.postgresql import UUID, JSONB, DATERANGE, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def pk(): return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
def now(): return mapped_column(DateTime(timezone=True), server_default=func.now())

class Role(str, enum.Enum):
    guest = "guest"; host = "host"; admin = "admin"

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(10), default="guest")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = now()

class Destination(Base):
    __tablename__ = "destinations"
    id: Mapped[uuid.UUID] = pk()
    city: Mapped[str] = mapped_column(String(100), index=True)
    country: Mapped[str] = mapped_column(String(100))
    image_url: Mapped[str] = mapped_column(String(500), default="")

class Property(Base):
    __tablename__ = "properties"
    id: Mapped[uuid.UUID] = pk()
    host_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("destinations.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(40), index=True, default="apartment")
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), index=True)
    cleaning_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    bedrooms: Mapped[int] = mapped_column(Integer, default=1)
    bathrooms: Mapped[int] = mapped_column(Integer, default=1)
    max_guests: Mapped[int] = mapped_column(Integer, default=2)
    min_nights: Mapped[int] = mapped_column(Integer, default=1)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    amenities: Mapped[dict] = mapped_column(JSONB, default=list)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = now()
    destination: Mapped[Destination] = relationship(lazy="joined")
    __table_args__ = (CheckConstraint("price_per_night > 0"),)

class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[uuid.UUID] = pk()
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"), index=True)
    guest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    guests: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), default="pending")  # pending|confirmed|cancelled|expired
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cleaning_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    service_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    taxes: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stay = mapped_column(DATERANGE, Computed("daterange(check_in, check_out, '[)')", persisted=True))
    created_at: Mapped[datetime] = now()
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="ck_booking_dates"),
        ExcludeConstraint(("property_id", "="), ("stay", "&&"), using="gist",
                          where=text("status IN ('pending','confirmed')"), name="ex_no_overlap"),
    )
