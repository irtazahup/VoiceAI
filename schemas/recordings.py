from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RecordingCreate(BaseModel):
    title: str
    filename: str
    file_path: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    file_type: Optional[str] = None


class RecordingUpdate(BaseModel):
    title: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: Optional[str] = None
    status: Optional[str] = None


class RecordingResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_size: Optional[int]
    duration: Optional[float]
    file_type: Optional[str]
    transcript: Optional[str]
    summary: Optional[str]
    action_items: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    user_id: int

    class Config:
        from_attributes = True


class RecordingList(BaseModel):
    recordings: list[RecordingResponse]
    total: int
