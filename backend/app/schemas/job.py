import uuid

from pydantic import BaseModel


class TranscribeRequest(BaseModel):
    visit_id: uuid.UUID


class TranscribeResponse(BaseModel):
    job_id: uuid.UUID
    upload_url: str
    upload_fields: dict[str, str]
