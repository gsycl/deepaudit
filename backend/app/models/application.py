import uuid
import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Numeric, Integer, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class ProgramType(str, enum.Enum):
    UNEMPLOYMENT = "unemployment"
    MEDICARE = "medicare"
    SNAP = "snap"
    DISABILITY = "disability"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    FLAGGED = "flagged"
    UNDER_REVIEW = "under_review"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applicants.id", ondelete="CASCADE"), index=True)
    program_type: Mapped[ProgramType] = mapped_column(SAEnum(ProgramType), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(SAEnum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    weekly_benefit_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    claim_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    claim_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    ai_recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_key_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="applications")
    employment_history: Mapped[list["EmploymentHistory"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    weekly_certifications: Mapped[list["WeeklyCertification"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    fraud_signals: Mapped[list["FraudSignal"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    submission_metadata: Mapped["SubmissionMetadata | None"] = relationship(back_populates="application", cascade="all, delete-orphan", uselist=False)
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="application", cascade="all, delete-orphan")
