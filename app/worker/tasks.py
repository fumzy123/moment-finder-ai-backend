import time
import logging
from app.worker.celery_app import celery_app
from app.db.database import SessionLocal
from app.models.video_metadata import VideoMetadata, VideoStatus
from app.models.character_screenshot_metadata import CharacterScreenshotMetadata
from app.models.moment import CharacterMoment

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_character_search")
def process_character_search(self, screenshot_db_id: str):
    """
    This is the background task that will eventually run the heavy AI computer vision.
    For now, it is a 'stub' that simulates work and updates the database.
    """
    logger.info(f"Worker picked up job for screenshot ID: {screenshot_db_id}")
    
    db = SessionLocal()
    try:
        # Step 1: Fetch the specific CharacterScreenshot row from PostgreSQL
        screenshot = db.query(CharacterScreenshotMetadata).filter(CharacterScreenshotMetadata.id == screenshot_db_id).first()
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_db_id} not found.")
            return {"status": "error", "message": "Screenshot not found"}

        # Step 2: Fetch the parent Video row and update status to ANALYZING
        video = db.query(VideoMetadata).filter(VideoMetadata.id == screenshot.video_id).first()
        if not video:
            logger.error(f"Parent Video ID {screenshot.video_id} not found.")
            return {"status": "error", "message": "Video not found"}

        logger.info(f"Analyzing Video '{video.original_filename}' for character '{screenshot.character_name}'...")
        video.status = VideoStatus.ANALYZING
        db.commit()

        # Step 3 & 4: Simulate the heavy AI processing (Computer Vision)
        logger.info("Starting heavy computer vision processing...")
        time.sleep(10) # Simulating GPU processing time
        
        # Step 5: Save the AI Results (Mocking finding the character twice)
        logger.info("AI Analysis complete. Saving discovered moments to database...")
        
        moment_1 = CharacterMoment(
            video_id=video.id,
            character_id=screenshot.id,
            action=f"Found {screenshot.character_name} looking dramatic",
            start_timestamp=15.5, # 15.5 seconds into the video
            end_timestamp=22.0,
            confidence_score=0.96
        )
        
        moment_2 = CharacterMoment(
            video_id=video.id,
            character_id=screenshot.id,
            action=f"Found {screenshot.character_name} walking",
            start_timestamp=105.0, # 1m 45s into the video
            end_timestamp=112.5,
            confidence_score=0.88
        )
        
        db.add_all([moment_1, moment_2])
        
        # Step 6: Completion
        screenshot.is_processed = True
        video.status = VideoStatus.COMPLETED
        
        db.commit()
        logger.info(f"Finished processing screenshot ID: {screenshot_db_id} Successfully!")
        
        return {"status": "success", "message": "AI Processing Complete", "screenshot_id": screenshot_db_id}
        
    except Exception as e:
        logger.error(f"Error during Celery processing: {e}")
        db.rollback()
        
        # Attempt to perfectly mark the video as FAILED
        try:
            video = db.query(VideoMetadata).filter(VideoMetadata.id == screenshot.video_id).first()
            if video:
                video.status = VideoStatus.FAILED
                video.error_message = str(e)
                db.commit()
        except Exception:
            pass # Ignore secondary fails
            
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
