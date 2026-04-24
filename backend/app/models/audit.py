import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class AuditAction(str, enum.Enum):
    APPROVED = "approved"
    DENIED = "denied"
    FLAGGED = "flagged"
    REANALYZED = "reanalyzed"
    VIEWED = "viewed"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    auditor_name: Mapped[str] = mapped_column(String(200))
    action: Mapped[AuditAction] = mapped_column(SAEnum(AuditAction))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application: Mapped["Application"] = relationship(back_populates="audit_logs")
