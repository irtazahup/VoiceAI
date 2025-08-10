from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Summary(Base):
    __tablename__ = 'summaries'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text)  # The actual summary text
    action_items = Column(Text)  # JSON string of action items
    key_points = Column(Text)  # JSON string of key points
    
    # Processing status
    status = Column(String, default='pending')  # pending, processing, completed, error
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to recording
    recording_id = Column(Integer, ForeignKey('recordings.id', ondelete="CASCADE"), unique=True)
    
    # Relationship
    recording = relationship('Recording', back_populates='summary_obj')
