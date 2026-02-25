from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.storage import storage_service

router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)

@router.get("/")
async def get_videos():
    """
    Retrieves all uploaded videos, their metadata, and a temporary pre-signed URL for playback.
    """
    try:
        videos = storage_service.list_videos()
        return {
            "status": "success",
            "count": len(videos),
            "videos": videos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Endpoint for uploading a video file to our S3/MinIO storage bucket.
    """
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video.")
        
    try:
        # FastAPI's UploadFile exposes the underlying spooled file object via `.file`
        object_key = storage_service.upload_file(file.file, file.filename, file.content_type)
        
        return {
            "status": "success",
            "message": "Video uploaded successfully",
            "video_id": object_key,
            "original_filename": file.filename
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
        "query": query,
        "matches": []
    }
