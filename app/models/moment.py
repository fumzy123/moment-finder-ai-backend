import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class CharacterMoment(Base):
    """
    Represents an actual AI discovery inside the video.
    """
    __tablename__ = "character_moments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys linking to BOTH the video and the specific character screenshot used as reference
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    character_id = Column(UUID(as_uuid=True), ForeignKey("video_screenshots.id"), nullable=False)
    
    # The AI Result
    action = Column(String, nullable=False) # e.g. "snapping fingers"
    start_timestamp = Column(Float, nullable=False) # In seconds
    end_timestamp = Column(Float, nullable=False) # In seconds
    
    confidence_score = Column(Float, nullable=False) # e.g. 0.98
    thumbnail_url = Column(String, nullable=True) # A visual thumbnail of the found moment
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("Video", back_populates="moments")
    character = relationship("VideoScreenshot", back_populates="moments")
