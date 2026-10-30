from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    passenger_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="passenger")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    card: Mapped["SmartCard"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    qr_token: Mapped["QRToken"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class SmartCard(Base):
    __tablename__ = "smart_cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    balance: Mapped[float] = mapped_column(Float, default=0)
    user: Mapped[User] = relationship(back_populates="card")

class QRToken(Base):
    __tablename__ = "qr_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="qr_token")

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    transaction_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Journey(Base):
    __tablename__ = "journeys"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    passenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    conductor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    from_stop: Mapped[str] = mapped_column(String(100))
    to_stop: Mapped[str] = mapped_column(String(100))
    distance_stops: Mapped[int] = mapped_column(Integer)
    fare: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
