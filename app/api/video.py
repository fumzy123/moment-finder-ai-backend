from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from app.services.file_storage_service import file_storage_service
from app.services.video_metadata_service import VideoMetadataStorageService, get_video_metadata_service
from app.services.character_screenshot_metadata_service import ScreenshotMetadataService, get_screenshot_metadata_service
from app.worker.tasks import process_character_search
router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)

@router.get("/")
async def get_videos(video_metadata_service: VideoMetadataStorageService = Depends(get_video_metadata_service)):
    """
    Retrieves all uploaded videos, their metadata, and a temporary pre-signed URL for playback.
    We merge data from the PostgreSQL database with signed URLs from MinIO.
    """
    try:
        # The router has no idea that a database even exists. It just asks the service for videos.
        db_videos = video_metadata_service.get_all_video_metadata()
        
        response_videos = []
        for v in db_videos:
            # Add the ephemeral signed URL for the frontend
            v["url"] = file_storage_service.get_presigned_url(v["storage_key"])
            response_videos.append(v)
            
        return {
            "status": "success",
            "count": len(response_videos),
            "videos": response_videos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...), 
    video_metadata_service: VideoMetadataStorageService = Depends(get_video_metadata_service)
):
    """
    Endpoint for uploading a video file to our S3/MinIO storage bucket,
    and simultaneously creating a tracking record via the Video Metadata Storage Service.
    """
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video.")
        
    try:
        # 1. Upload the physical massive file to MinIO via the File Storage Service
        # We store original videos in the 'videos/' prefix folder
        object_key = file_storage_service.upload_file(
            file.file, 
            file.filename, 
            file.content_type, 
            prefix="videos/"
        )
        
        # 2. Save the structured metadata via the Video Metadata Storage Service
        video_record = video_metadata_service.save_video_metadata(
            original_filename=file.filename, 
            storage_key=object_key
        )
        
        return {
            "status": "success",
            "message": "Video uploaded successfully",
            "video_id": video_record["id"],
            "original_filename": video_record["original_filename"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_video(query: str, character_name: str, video_id: str):
    """
    Endpoint to search for a specific character action within an uploaded video.
    *(MVP Note: This returns mock timestamp references based on the query).*
    """
    # Mock search logic
    if query.lower() == "drinking" and character_name.lower() == "rick":
        return {
            "status": "success",
            "video_id": video_id,
            "character": character_name,
            "query": query,
            "matches": [
                {"timestamp": "00:15:23", "confidence_score": 0.98},
                {"timestamp": "00:21:05", "confidence_score": 0.92}
            ]
        }
        
    return {
        "status": "success",
        "video_id": video_id,
        "character": character_name,
        "matches": []
    }

@router.post("/search/screenshot")
async def upload_screenshot_and_search(
    video_id: str = Form(...),
    character_name: str = Form(...),
    time_stamp: float = Form(...),
    file: UploadFile = File(...),
    screenshot_metadata_service: ScreenshotMetadataService = Depends(get_screenshot_metadata_service)
):
    """
    Endpoint for uploading a cropped character face to search the video.
    This triggers the asynchronous Celery background worker!
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
        
    try:
        # 1. Upload the physical image crop to MinIO
        # Neatly nest this inside the specific video's folder in MinIO
        prefix = f"videos/{video_id}/screenshots/"
        object_key = file_storage_service.upload_file(
            file.file, 
            file.filename, 
            file.content_type, 
            prefix=prefix
        )
        
        # 2. Save the metadata to PostgreSQL (CharacterScreenshot table)
        screenshot_record = screenshot_metadata_service.save_screenshot_metadata(
            video_id=video_id,
            character_name=character_name,
            storage_key=object_key,
            time_stamp=time_stamp
        )
        
        # 3. The Magic: Dispatch the job to Redis for Celery to pick up
        process_character_search.delay(screenshot_record["id"])
        
        # 4. Instantly return a success to the user so their browser doesn't freeze
        return {
            "status": "success",
            "message": f"Search started for {character_name}. AI is processing in the background.",
            "screenshot_id": screenshot_record["id"],
            "processing_status": "PROCESSING"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
