import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class CharacterScreenshotMetadata(Base):
    """
    Represents a specific character reference image cropped by the user.
    """
    __tablename__ = "character_screenshot_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key linking it to the master Video
    video_id = Column(UUID(as_uuid=True), ForeignKey("video_metadata.id"), nullable=False)
    
    # Data
    character_name = Column(String, nullable=False) # e.g., "Thanos"
    screenshot_url = Column(String, nullable=False) # The MinIO url for the crop
    time_stamp = Column(Float, nullable=False) # What second in the video it was cropped
    
    # AI Search Architecture
    is_processed = Column(Boolean, default=False) # True when we have generated vector embeddings for it
    vector_id = Column(String, nullable=True) # The ID connecting it to ChromaDB / pgvector
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    video = relationship("VideoMetadata", back_populates="screenshots")
    moments = relationship("CharacterMoment", back_populates="character")
