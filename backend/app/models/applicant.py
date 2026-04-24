import uuid
from datetime import datetime, date
from sqlalchemy import String, Date, DateTime, Boolean, Float, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Applicant(Base):
    __tablename__ = "applicants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ssn_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    dob: Mapped[date] = mapped_column(Date)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(255))
    is_deceased: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    addresses: Mapped[list["Address"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    financial_records: Mapped[list["FinancialRecord"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    household_members: Mapped[list["HouseholdMember"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applicants.id", ondelete="CASCADE"), index=True)
    street: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2))
    zip_code: Mapped[str] = mapped_column(String(10))
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    applicant: Mapped["Applicant"] = relationship(back_populates="addresses")


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applicants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    relationship_to_applicant: Mapped[str] = mapped_column(String(50))
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    ssn_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="household_members")
