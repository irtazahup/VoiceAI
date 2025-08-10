from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SummaryCreate(BaseModel):
    title: str
    content: Optional[str] = None
    action_items: Optional[str] = None
    key_points: Optional[str] = None


class SummaryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    action_items: Optional[str] = None
    key_points: Optional[str] = None
    status: Optional[str] = None


class SummaryResponse(BaseModel):
    id: int
    title: str
    content: Optional[str]
    action_items: Optional[str]
    key_points: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    recording_id: int

    class Config:
        from_attributes = True
