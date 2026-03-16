import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    preferred_language: str = "en"


class UserCreate(UserBase):
    clerk_user_id: str


class UserOut(UserBase):
    id: uuid.UUID
    clerk_user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
