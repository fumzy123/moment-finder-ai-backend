from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.character_screenshot_metadata import CharacterScreenshotMetadata
from app.db.database import get_db
import logging

logger = logging.getLogger(__name__)

class ScreenshotMetadataService:
    def __init__(self, db: Session):
        self.db = db

    def save_screenshot_metadata(self, video_id: str, character_name: str, storage_key: str, time_stamp: float) -> dict:
        """
        Saves metadata for a new CharacterScreenshot (character crop) in PostgreSQL.
        """
        try:
            db_screenshot = CharacterScreenshotMetadata(
                video_id=video_id,
                character_name=character_name,
                screenshot_url=storage_key,
                time_stamp=time_stamp
            )
            self.db.add(db_screenshot)
            self.db.commit()
            self.db.refresh(db_screenshot)
            
            return {
                "id": str(db_screenshot.id),
                "video_id": str(db_screenshot.video_id),
                "character_name": db_screenshot.character_name,
                "screenshot_url": db_screenshot.screenshot_url,
                "time_stamp": db_screenshot.time_stamp,
                "created_at": db_screenshot.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save screenshot metadata: {e}")
            raise Exception(f"Database error: {e}")

def get_screenshot_metadata_service(db: Session = Depends(get_db)) -> ScreenshotMetadataService:
    return ScreenshotMetadataService(db)
