from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Recording(Base):
    __tablename__ = 'recordings'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)  # Original filename
    file_path = Column(String, nullable=False)  # Path where file is stored
    file_size = Column(Integer)  # File size in bytes
    duration = Column(Float)  # Duration in seconds
    file_type = Column(String)  # e.g., 'mp3', 'm4a', 'wav'
    
    # AI-generated content
    transcript = Column(Text)  # Full transcription
    summary = Column(Text)  # Meeting summary
    action_items = Column(Text)  # Extracted action items (JSON string)
    
    # Processing status
    status = Column(String, default='uploaded')  # uploaded, processing, completed, error
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    
    # Relationship
    user = relationship('User', back_populates='recordings')
    summary_obj = relationship('Summary', back_populates='recording', uselist=False, cascade="all, delete-orphan")