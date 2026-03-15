import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Transcript(Base):
    __tablename__ = "transcripts"
    __table_args__ = (UniqueConstraint("visit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id", ondelete="CASCADE"))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunks: Mapped[list] = mapped_column(JSONB, default=list)
    language_detected: Mapped[str] = mapped_column(String(10), default="en")
    wer_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
