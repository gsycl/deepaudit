import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Date, DateTime, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class EmploymentHistory(Base):
    __tablename__ = "employment_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    employer_name: Mapped[str] = mapped_column(String(255))
    employer_ein_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    separation_reason: Mapped[str] = mapped_column(String(50))  # laid_off, quit, fired
    reported_salary: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    application: Mapped["Application"] = relationship(back_populates="employment_history")


class WeeklyCertification(Base):
    __tablename__ = "weekly_certifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    week_start: Mapped[date] = mapped_column(Date)
    did_work: Mapped[bool] = mapped_column(Boolean, default=False)
    reported_earnings: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    job_search_contacts: Mapped[int] = mapped_column(default=0)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submitted_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="weekly_certifications")
