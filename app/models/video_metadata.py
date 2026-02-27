import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class VideoStatus(enum.Enum):
    PENDING = "PENDING"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metadata
    original_filename = Column(String, nullable=False)
    storage_key = Column(String, nullable=False, unique=True) # e.g. the MinIO object key
    duration_seconds = Column(Integer, nullable=True) # Useful for frontend progress bars
    
    # AI Tracking
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False)
    error_message = Column(String, nullable=True) # If processing fails
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # This allows us to say `video.screenshots` to get all characters tracked in this video
    screenshots = relationship("CharacterScreenshotMetadata", back_populates="video", cascade="all, delete-orphan")
    moments = relationship("CharacterMoment", back_populates="video", cascade="all, delete-orphan")
