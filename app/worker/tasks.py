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
    # Step 1: Fetch the specific CharacterScreenshot row from PostgreSQL
    screenshot = db.query(CharacterScreenshotMetadata).filter(CharacterScreenshotMetadata.id == screenshot_db_id).first()
    if not screenshot:
        logger.error(f"Screenshot with ID {screenshot_db_id} not found.")
        db.close()
        return {"status": "error", "message": "Screenshot not found"}

    # Step 2: Fetch the parent Video row and update status to ANALYZING
    video = db.query(VideoMetadata).filter(VideoMetadata.id == screenshot.video_id).first()
    if not video:
        logger.error(f"Parent Video ID {screenshot.video_id} not found.")
        db.close()
        return {"status": "error", "message": "Video not found"}

    logger.info(f"Analyzing Video '{video.original_filename}' for character '{screenshot.character_name}'...")
    video.status = VideoStatus.ANALYZING
    db.commit()

    import os
    from app.services.file_storage_service import file_storage_service
    from app.services.ai.factory import get_ai_engine
    
    # Define temporary file paths to hold the MinIO files during processing
    temp_video_path = f"/tmp/{video.id}.mp4"
    temp_img_path = f"/tmp/{screenshot.id}.png"
    
    # Ensure /tmp exists on Windows or Linux
    os.makedirs("/tmp", exist_ok=True)
    
    try:
        # Step 3: Download the physical files from MinIO to the local Worker machine
        logger.info(f"Downloading files from Storage to local worker for analysis...")
        file_storage_service.download_file(video.storage_key, temp_video_path)
        file_storage_service.download_file(screenshot.screenshot_url, temp_img_path)
        
        # Step 4: Load the active AI Engine and perform the analysis
        logger.info(f"Sending files to the AI Engine for character '{screenshot.character_name}'...")
        ai_engine = get_ai_engine()
        moments_data = ai_engine.find_character_moments(
            video_file_path=temp_video_path,
            screenshot_file_path=temp_img_path,
            character_name=screenshot.character_name
        )
        
        # Step 5: Save the AI Results dynamically
        logger.info(f"AI Analysis complete! Discovered {len(moments_data)} moments. Saving to database...")
        moments_to_insert = []
        for moment_dict in moments_data:
            moment = CharacterMoment(
                video_id=video.id,
                character_id=screenshot.id,
                action=moment_dict.get("action", f"Found {screenshot.character_name}"),
                start_timestamp=moment_dict.get("start_timestamp", 0.0),
                end_timestamp=moment_dict.get("end_timestamp", 0.0),
                confidence_score=moment_dict.get("confidence_score", 0.0)
            )
            moments_to_insert.append(moment)
            
        if moments_to_insert:
            db.add_all(moments_to_insert)
        
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
        # Step 7: Clean up the local hard drive
        logger.info("Cleaning up local temporary files...")
        try:
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
        except Exception as cleanup_error:
            logger.error(f"Failed to delete local temp files: {cleanup_error}")
            
        db.close()
