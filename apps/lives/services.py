"""
Services for live sessions - recording uploads and processing
"""
import os
import hashlib
import uuid
from typing import Optional
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from apps.files.services import SecureFileService
from apps.files.models import File, FileType
from .models import Live

logger = __import__('logging').getLogger(__name__)

# Initialize file service
file_service = SecureFileService()


def upload_recording_to_minio(
    live: Live,
    recording_file_path: str,
    recording_filename: str = None
) -> Optional[File]:
    """
    Upload a Jitsi recording file to MinIO and create File record
    
    Args:
        live: Live session instance
        recording_file_path: Path to the recording file (local file system)
        recording_filename: Optional custom filename
        
    Returns:
        File instance if successful, None otherwise
    """
    try:
        if not os.path.exists(recording_file_path):
            logger.error(f"Recording file not found: {recording_file_path}")
            return None
        
        # Get file stats
        file_size = os.path.getsize(recording_file_path)
        file_extension = os.path.splitext(recording_file_path)[1] or '.mp4'
        
        # Generate filename if not provided
        if not recording_filename:
            recording_filename = f"live-{live.id}-{timezone.now().strftime('%Y%m%d-%H%M%S')}{file_extension}"
        
        # Read file and calculate checksum
        with open(recording_file_path, 'rb') as f:
            file_content = f.read()
            checksum = hashlib.sha256(file_content).hexdigest()
        
        # Determine MIME type
        mime_type = 'video/mp4'
        if file_extension == '.mkv':
            mime_type = 'video/x-matroska'
        elif file_extension == '.webm':
            mime_type = 'video/webm'
        
        # Generate secure file path in MinIO
        secure_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"protected/videos/lives/{secure_filename}"
        
        # Upload to MinIO
        try:
            file_service.minio_client.put_object(
                bucket_name=file_service.bucket_name,
                object_name=file_path,
                data=BytesIO(file_content),
                length=file_size,
                content_type=mime_type
            )
            logger.info(f"Recording uploaded to MinIO: {file_path}")
        except Exception as e:
            logger.error(f"Error uploading recording to MinIO: {e}")
            return None
        
        # Create File record
        file_obj = File.objects.create(
            name=recording_filename,
            original_name=recording_filename,
            file_path=file_path,
            file_type=FileType.VIDEO,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=live.professor.user,
            checksum=checksum,
            access_level='student',  # Recordings accessible to students
            course=live.module,  # Link to module if available
            chapter=live.chapter,  # Link to chapter if available
        )
        
        # Generate signed URL for recording (long expiration for recordings)
        try:
            recording_url = file_service.generate_signed_url(
                file=file_obj,
                user=live.professor.user,
                access_type='stream',
                expires_in=31536000  # 1 year expiration for recordings
            )
            # Update live with signed URL
            live.recording_url = recording_url
        except Exception as e:
            logger.warning(f"Could not generate signed URL, using file path: {e}")
            # Fallback to file path if signed URL fails
            from django.conf import settings
            if hasattr(settings, 'MINIO_ENDPOINT_URL'):
                endpoint = settings.MINIO_ENDPOINT_URL.replace('http://', '').replace('https://', '')
                live.recording_url = f"{settings.MINIO_ENDPOINT_URL}/{file_service.bucket_name}/{file_path}"
            else:
                live.recording_url = f"/files/{file_obj.id}/access"
        
        # Update live with recording info
        live.recording_file = file_obj
        live.save()
        
        logger.info(f"Recording file created for live {live.id}: {file_obj.id}")
        return file_obj
            
    except Exception as e:
        logger.error(f"Error uploading recording to MinIO: {e}")
        return None


def upload_recording_from_file_object(
    live: Live,
    file_object: InMemoryUploadedFile
) -> Optional[File]:
    """
    Upload a recording file object (from HTTP request) to MinIO
    
    Args:
        live: Live session instance
        file_object: File object from request.FILES
        
    Returns:
        File instance if successful, None otherwise
    """
    try:
        file_extension = os.path.splitext(file_object.name)[1] or '.mp4'
        recording_filename = f"live-{live.id}-{timezone.now().strftime('%Y%m%d-%H%M%S')}{file_extension}"
        
        # Read file content
        file_content = file_object.read()
        file_size = len(file_content)
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Determine MIME type
        mime_type = file_object.content_type or 'video/mp4'
        
        # Generate secure file path in MinIO
        secure_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"protected/videos/lives/{secure_filename}"
        
        # Upload to MinIO
        try:
            file_service.minio_client.put_object(
                bucket_name=file_service.bucket_name,
                object_name=file_path,
                data=BytesIO(file_content),
                length=file_size,
                content_type=mime_type
            )
            logger.info(f"Recording uploaded to MinIO: {file_path}")
        except Exception as e:
            logger.error(f"Error uploading recording to MinIO: {e}")
            return None
        
        # Create File record
        file_obj = File.objects.create(
            name=recording_filename,
            original_name=file_object.name,
            file_path=file_path,
            file_type=FileType.VIDEO,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=live.professor.user,
            checksum=checksum,
            access_level='student',
            course=live.module,
            chapter=live.chapter,
        )
        
        # Generate signed URL
        try:
            recording_url = file_service.generate_signed_url(
                file=file_obj,
                user=live.professor.user,
                access_type='stream',
                expires_in=31536000
            )
            live.recording_url = recording_url
        except Exception as e:
            logger.warning(f"Could not generate signed URL, using file path: {e}")
            # Fallback to file path if signed URL fails
            from django.conf import settings
            if hasattr(settings, 'MINIO_ENDPOINT_URL'):
                endpoint = settings.MINIO_ENDPOINT_URL.replace('http://', '').replace('https://', '')
                live.recording_url = f"{settings.MINIO_ENDPOINT_URL}/{file_service.bucket_name}/{file_path}"
            else:
                live.recording_url = f"/files/{file_obj.id}/access"
        
        live.recording_file = file_obj
        live.save()
        
        logger.info(f"Recording file created for live {live.id}: {file_obj.id}")
        return file_obj
            
    except Exception as e:
        logger.error(f"Error uploading recording file object: {e}")
        return None

