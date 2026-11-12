import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
def created(): return mapped_column(DateTime(timezone=True), server_default=func.now())

class RefreshSession(Base):
    __tablename__ = 'refresh_sessions'
    id: Mapped[uuid.UUID] = uid()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = created()

class Favorite(Base):
    __tablename__ = 'favorites'
    id: Mapped[uuid.UUID] = uid()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('properties.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = created()
    __table_args__ = (UniqueConstraint('user_id','property_id', name='uq_favorite_user_property'),)

class Review(Base):
    __tablename__ = 'reviews'
    id: Mapped[uuid.UUID] = uid()
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('properties.id', ondelete='CASCADE'), index=True)
    guest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('bookings.id', ondelete='CASCADE'), unique=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = created()

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[uuid.UUID] = uid()
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True, index=True)
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = created()

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[uuid.UUID] = uid()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = created()

class Payment(Base):
    __tablename__ = 'payments'
    id: Mapped[uuid.UUID] = uid()
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('bookings.id', ondelete='CASCADE'), unique=True)
    provider: Mapped[str] = mapped_column(String(30), default='stripe')
    provider_reference: Mapped[str] = mapped_column(String(255), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(10,2))
    currency: Mapped[str] = mapped_column(String(3), default='usd')
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = created()

class EmailToken(Base):
    __tablename__ = 'email_tokens'
    id: Mapped[uuid.UUID] = uid()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    id: Mapped[uuid.UUID] = uid()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()
