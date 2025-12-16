"""
S3 service for video uploads and streaming
"""
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict
import uuid
from datetime import datetime
from src.config import get_settings
from src.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class S3Service:
    """Service for S3 operations"""
    
    def __init__(self):
        self.settings = settings
        self.client = boto3.client(
            's3',
            endpoint_url=self.settings.s3_endpoint,
            aws_access_key_id=self.settings.s3_access_key,
            aws_secret_access_key=self.settings.s3_secret_key,
            region_name=self.settings.s3_region,
            use_ssl=self.settings.s3_use_ssl
        )
        logger.info("S3 client initialized")
    
    def generate_upload_url(
        self,
        filename: str,
        user: User,
        is_public: bool,
        tags: list[str],
        allowed_users: list[str],
        expires_in: int = 3600
    ) -> Dict[str, any]:
        """
        Generate presigned URL for video upload
        
        Args:
            filename: Original filename
            user: Uploading user
            is_public: Whether video is public
            tags: Video tags
            allowed_users: Additional allowed users
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with upload_url, object_key, expires_in, metadata
        """
        try:
            # Generate unique object key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = filename.split('.')[-1] if '.' in filename else 'mp4'
            object_key = f"{user.normalized_username}/{timestamp}_{unique_id}.{file_extension}"
            
            # Prepare metadata
            # S3 metadata keys must be lowercase and cannot contain spaces
            metadata = {
                'owner': user.username,
                'is-public': str(is_public).lower(),
                'original-filename': filename,
                'upload-timestamp': datetime.utcnow().isoformat()
            }
            
            # Add tags as comma-separated string
            if tags:
                metadata['tags'] = ','.join(tags)
            
            # Add allowed users as comma-separated string (if not public)
            if not is_public and allowed_users:
                # Always include owner in allowed users
                all_allowed = [user.username] + [u for u in allowed_users if u != user.username]
                metadata['allowed-users'] = ','.join(all_allowed)
            elif not is_public:
                # Private video with only owner
                metadata['allowed-users'] = user.username
            
            logger.info(f"Generating upload URL for {object_key}")
            logger.debug(f"Metadata: {metadata}")
            
            # Prepare S3 metadata fields for presigned POST
            # IMPORTANT: All metadata must be included in Fields for presigned POST
            s3_fields = {
                'x-amz-meta-owner': metadata['owner'],
                'x-amz-meta-is-public': metadata['is-public'],
                'x-amz-meta-original-filename': metadata['original-filename'],
                'x-amz-meta-upload-timestamp': metadata['upload-timestamp']
            }
            
            # Add tags if present
            if 'tags' in metadata:
                s3_fields['x-amz-meta-tags'] = metadata['tags']
            
            # Add allowed-users if present
            if 'allowed-users' in metadata:
                s3_fields['x-amz-meta-allowed-users'] = metadata['allowed-users']
            
            # Generate presigned POST URL
            presigned_post = self.client.generate_presigned_post(
                Bucket=self.settings.s3_upload_bucket,
                Key=object_key,
                Fields=s3_fields,
                Conditions=[
                    ['content-length-range', 1, self.settings.max_upload_size_mb * 1024 * 1024]
                ],
                ExpiresIn=expires_in
            )
            
            logger.info(f"Upload URL generated for {object_key}, expires in {expires_in}s")
            
            return {
                'upload_url': presigned_post['url'],
                'fields': presigned_post['fields'],
                'object_key': object_key,
                'expires_in': expires_in,
                'metadata': metadata
            }
            
        except ClientError as e:
            logger.error(f"Error generating upload URL: {str(e)}")
            raise
    
    async def upload_file(
        self,
        file,
        user: User,
        is_public: bool,
        tags: list[str],
        allowed_users: list[str]
    ) -> str:
        """
        Upload file directly to S3 (backend proxy)
        
        Args:
            file: UploadFile from FastAPI
            user: Uploading user
            is_public: Whether video is public
            tags: Video tags
            allowed_users: Additional allowed users
            
        Returns:
            S3 object key
        """
        try:
            # Use username for S3 path (human-readable)
            username = user.username
            
            # Generate unique object key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = uuid.uuid4().hex[:8]
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
            object_key = f"{username}/{timestamp}_{unique_id}.{file_ext}"
            
            # NEW LOGIC: Default is_public=True, always populate allowed_users with uploader
            # If user unchecks "Make this video private", is_public=True (default)
            # If user checks "Make this video private", is_public=False
            actual_is_public = is_public  # is_public from form (True by default in GUI)
            
            # Always add uploader to allowed_users (regardless of is_public)
            all_allowed_users = [username]
            if allowed_users:
                # Add any additional users specified by uploader
                all_allowed_users.extend([u for u in allowed_users if u and u != username])
            
            # Prepare metadata
            metadata = {
                'is-public': 'true' if actual_is_public else 'false',
                'allowed-users': ','.join(all_allowed_users),  # Always populated
                'original-filename': file.filename,
                'upload-timestamp': datetime.utcnow().isoformat()
            }
            
            # Add tags if present
            if tags:
                metadata['tags'] = ','.join(tags)
            
            logger.info(f"Uploading {file.filename} to s3://{self.settings.s3_upload_bucket}/{object_key}")
            logger.info(f"Metadata to set: {metadata}")
            
            # Ensure file pointer is at the beginning
            await file.seek(0)
            
            # Read the entire file content
            file_content = await file.read()
            logger.info(f"Read {len(file_content)} bytes from uploaded file")
            
            # Upload file to S3 using put_object (for in-memory upload)
            response = self.client.put_object(
                Bucket=self.settings.s3_upload_bucket,
                Key=object_key,
                Body=file_content,
                Metadata=metadata
            )
            
            logger.info(f"File uploaded to S3: {object_key} ({len(file_content)} bytes)")
            logger.info(f"S3 put_object response ETag: {response.get('ETag')}")
            
            return object_key
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise
    
    def generate_download_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for video download/streaming
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            logger.info(f"Generated download URL for s3://{bucket}/{key}")
            logger.info(f"Presigned URL endpoint: {url.split('?')[0]}")  # Log URL without signature
            return url
            
        except ClientError as e:
            logger.error(f"Error generating download URL: {str(e)}")
            raise
    
    def get_object_metadata(self, bucket: str, key: str) -> Dict:
        """
        Get metadata for an S3 object
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Metadata dict
        """
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return response.get('Metadata', {})
        except ClientError as e:
            logger.error(f"Error getting object metadata: {str(e)}")
            raise
    
    def stream_video(self, bucket: str, key: str):
        """
        Stream video content from S3 as an iterator
        
        This method returns a generator that yields video chunks,
        suitable for use with FastAPI's StreamingResponse.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Yields:
            Video data chunks
        """
        try:
            logger.info(f"Streaming video from s3://{bucket}/{key}")
            
            # Get object from S3
            response = self.client.get_object(Bucket=bucket, Key=key)
            
            # Stream the body in chunks
            chunk_size = 64 * 1024  # 64KB chunks
            for chunk in response['Body'].iter_chunks(chunk_size=chunk_size):
                yield chunk
            
            logger.debug(f"Finished streaming s3://{bucket}/{key}")
            
        except ClientError as e:
            logger.error(f"Error streaming video from S3: {str(e)}")
            raise


# Global S3 service instance
_s3_service: S3Service | None = None


def get_s3_service() -> S3Service:
    """Get or create global S3 service instance"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service

