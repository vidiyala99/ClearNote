import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.db.models.visit import VisitStatus


class VisitBase(BaseModel):
    title: str
    visit_date: date
    doctor_name: str | None = None
    consent_at: datetime


class VisitCreate(VisitBase):
    pass


class VisitOut(VisitBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: VisitStatus
    audio_s3_key: str | None = None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
