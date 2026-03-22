import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UrgencyTag(str, enum.Enum):
    normal = "normal"
    follow_up = "follow-up"
    referral = "referral"
    prescription = "prescription"
    urgent = "urgent"


class Summary(Base):
    __tablename__ = "summaries"
    __table_args__ = (UniqueConstraint("visit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    visit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("visits.id"))
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    medications: Mapped[list] = mapped_column(JSONB, default=list)
    diagnoses: Mapped[list] = mapped_column(JSONB, default=list)
    action_items: Mapped[list] = mapped_column(JSONB, default=list)
    urgency_tag: Mapped[UrgencyTag] = mapped_column(
        SAEnum(UrgencyTag, name="urgency_tag"), default=UrgencyTag.normal
    )
    translated_overview: Mapped[str | None] = mapped_column(Text, nullable=True)
