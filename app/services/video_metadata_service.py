from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.video import Video, VideoStatus
from app.db.database import get_db
from app.db.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class VideoMetadataStorageService:
    def __init__(self, db: Session):
        # The database session is initialized once per request and passed in
        self.db = db

    def save_video_metadata(self, original_filename: str, storage_key: str) -> dict:
        """
        Saves metadata for a new Video record in the PostgreSQL database.
        Returns a dictionary to fully decouple SQLAlchemy models from the API layer.
        """
        try:
            db_video = Video(
                original_filename=original_filename,
                storage_key=storage_key,
                status=VideoStatus.PENDING # Initial status upon upload
            )
            self.db.add(db_video)
            self.db.commit()
            self.db.refresh(db_video) # Reload the object to get the newly generated UUID
            
            # Convert to dict so the router doesn't know about SQLAlchemy objects at all
            return {
                "id": str(db_video.id),
                "original_filename": db_video.original_filename,
                "status": db_video.status.value,
                "duration_seconds": db_video.duration_seconds,
                "storage_key": db_video.storage_key,
                "created_at": db_video.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback() # If something fails, undo the database transaction
            logger.error(f"Failed to create video record in database: {e}")
            raise Exception(f"Database error: {e}")

    def get_all_video_metadata(self) -> list[dict]:
        """
        Retrieves metadata for all video tracking records from the database.
        Returns a list of dictionaries to fully decouple SQLAlchemy models from the API layer.
        """
        videos = self.db.query(Video).order_by(Video.created_at.desc()).all()
        return [
                {
                    "id": str(v.id),
                    "original_filename": v.original_filename,
                    "status": v.status.value,
                    "duration_seconds": v.duration_seconds,
                    "storage_key": v.storage_key,
                    "created_at": v.created_at.isoformat()
                }
                for v in videos
            ]

# We construct a dependency that FastAPI will automatically call.
# It gets a database session from `get_db()`, instantiates our Service, and passes it to the router!
def get_video_metadata_service(db: Session = Depends(get_db)) -> VideoMetadataStorageService:
    return VideoMetadataStorageService(db)
