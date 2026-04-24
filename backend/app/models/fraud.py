import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class SignalSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudSignal(Base):
    __tablename__ = "fraud_signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str] = mapped_column(String(20))
    signal_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[SignalSeverity] = mapped_column(SAEnum(SignalSeverity))
    score_contribution: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    signal_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application: Mapped["Application"] = relationship(back_populates="fraud_signals")
