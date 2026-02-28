import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class FileStorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            use_ssl=settings.S3_USE_SSL
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_file(self, file_obj, filename: str, content_type: str, prefix: str = "") -> str:
        """
        Uploads a file object to S3 / MinIO and returns the generated object key.
        Supports optional prefixes (e.g., 'videos/' or 'videos/{id}/screenshots/').
        """
        # Generate a unique key for the file to prevent overwrites
        extension = filename.split('.')[-1] if '.' in filename else ''
        file_uuid = uuid.uuid4().hex
        unique_key = f"{prefix}{file_uuid}.{extension}" if extension else f"{prefix}{file_uuid}"
        
        try:
            # We store the original filename in the object metadata
            # S3/MinIO metadata values shouldn't contain non-ASCII characters, so we handle that safely.
            safe_filename = filename.encode('ascii', 'ignore').decode() or "unknown_video"
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                unique_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': {'original-filename': safe_filename}
                }
            )
            return unique_key
        except ClientError as e:
            logger.error(f"Error uploading file to storage: {e}")
            raise Exception("Failed to upload video to storage")

    def get_presigned_url(self, object_key: str, expiration_seconds: int = 3600) -> str:
        """
        Generates a secure, temporary URL to access the video file directly from the browser.
        """
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration_seconds
            )
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return ""

    def download_file(self, object_key: str, download_path: str) -> str:
        """
        Downloads a file from S3 / MinIO to the local filesystem.
        Used by the background Celery Workers to fetch physical files for AI processing.
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_key, download_path)
            return download_path
        except ClientError as e:
            logger.error(f"Error downloading file {object_key} from storage: {e}")
            raise Exception("Failed to download file from storage")

    def list_videos(self) -> list:
        """
        Retrieves all videos from the bucket, fetches their original filenames from metadata, 
        and generates playable pre-signed URLs.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            videos = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    size = obj['Size']
                    last_modified = obj['LastModified'].isoformat()
                    
                    # Fetch metadata to get the original filename we saved during upload
                    head_response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
                    metadata = head_response.get('Metadata', {})
                    original_name = metadata.get('original-filename', key)
                    
                    presigned_url = self.get_presigned_url(key)
                    
                    videos.append({
                        "video_id": key,
                        "original_filename": original_name,
                        "size_bytes": size,
                        "uploaded_at": last_modified,
                        "url": presigned_url
                    })
                    
            return sorted(videos, key=lambda x: x['uploaded_at'], reverse=True)
            
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            raise Exception("Failed to retrieve videos from storage")

file_storage_service = FileStorageService()
