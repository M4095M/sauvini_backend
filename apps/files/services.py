"""
Secure file service for handling file operations with security
"""
import os
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from minio import Minio
from minio.error import S3Error
import logging

from .models import File, FileAccess, FileAccessLog, FileUploadSession, FileAccessLevel

logger = logging.getLogger(__name__)


class SecureFileService:
    """Service for secure file operations"""
    
    def __init__(self):
        # Parse the endpoint URL correctly
        endpoint_url = settings.MINIO_ENDPOINT_URL
        if endpoint_url.startswith('http://'):
            endpoint = endpoint_url.replace('http://', '')
            secure = False
        elif endpoint_url.startswith('https://'):
            endpoint = endpoint_url.replace('https://', '')
            secure = True
        else:
            endpoint = endpoint_url
            secure = settings.MINIO_USE_HTTPS
        
        self.minio_client = Minio(
            endpoint=endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )
        self.bucket_name = settings.MINIO_STORAGE_BUCKET_NAME
    
    def generate_signed_url(self, file: File, user, access_type: str = 'read', expires_in: int = 3600) -> str:
        """
        Generate a signed URL for secure file access
        
        Args:
            file: File object
            user: User requesting access
            access_type: Type of access (read, download, stream)
            expires_in: URL expiration time in seconds
            
        Returns:
            Signed URL for file access
            
        Raises:
            PermissionDenied: If user doesn't have access
        """
        # Verify user has access to this file
        if not self.verify_file_access(file, user, access_type):
            self.log_access_attempt(file, user, access_type, False, "Access denied")
            raise PermissionDenied("You don't have permission to access this file")
        
        try:
            # Generate signed URL
            signed_url = self.minio_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file.file_path,
                expires=timedelta(seconds=expires_in)
            )
            
            # Log successful access
            self.log_access_attempt(file, user, access_type, True)
            
            # Update access count
            self.update_access_count(file, user, access_type)
            
            return signed_url
            
        except S3Error as e:
            logger.error(f"Error generating signed URL for file {file.id}: {e}")
            self.log_access_attempt(file, user, access_type, False, str(e))
            raise ValidationError("Error generating file access URL")
    
    def verify_file_access(self, file: File, user, access_type: str = 'read') -> bool:
        """
        Verify if user has access to the file
        
        Args:
            file: File object
            user: User requesting access
            access_type: Type of access requested
            
        Returns:
            True if user has access, False otherwise
        """
        # Check if file is active and not expired
        if not file.is_active or file.is_expired:
            return False
        
        # Check access level
        if not self.check_access_level(file, user):
            return False
        
        # Check specific file access permissions
        if not self.check_file_access_permissions(file, user, access_type):
            return False
        
        # Check course/chapter/lesson access
        if not self.check_content_access(file, user):
            return False
        
        return True
    
    def check_access_level(self, file: File, user) -> bool:
        """Check if user meets the file's access level requirements"""
        if file.access_level == FileAccessLevel.PUBLIC:
            return True
        
        # Determine user role based on related models
        user_role = self.get_user_role(user)
        
        if file.access_level == FileAccessLevel.STUDENT:
            return user_role in ['student', 'professor', 'admin']
        
        if file.access_level == FileAccessLevel.PROFESSOR:
            return user_role in ['professor', 'admin']
        
        if file.access_level == FileAccessLevel.ADMIN:
            return user_role == 'admin'
        
        return False
    
    def get_user_role(self, user) -> str:
        """Determine user role based on related models"""
        if hasattr(user, 'admin'):
            return 'admin'
        elif hasattr(user, 'professor'):
            return 'professor'
        elif hasattr(user, 'student'):
            return 'student'
        else:
            return 'user'
    
    def check_file_access_permissions(self, file: File, user, access_type: str) -> bool:
        """Check specific file access permissions"""
        # Check if access type is allowed for this file
        if access_type == 'download' and not file.allow_download:
            return False
        
        if access_type == 'stream' and not file.allow_streaming:
            return False
        
        # Check for explicit file access grants
        try:
            file_access = FileAccess.objects.get(
                file=file,
                user=user,
                access_type=access_type
            )
            
            # Check if access has expired
            if file_access.is_expired:
                return False
            
            # Check download limits
            if access_type == 'download' and file.max_downloads:
                if file_access.access_count >= file.max_downloads:
                    return False
            
            return True
            
        except FileAccess.DoesNotExist:
            # No explicit access granted, check if user has general access
            return self.check_access_level(file, user)
    
    def check_content_access(self, file: File, user) -> bool:
        """Check if user has access to the content this file belongs to"""
        # If file is not associated with any content, allow based on access level
        if not file.course and not file.chapter and not file.lesson:
            return self.check_access_level(file, user)
        
        # Check course access
        if file.course:
            # Add course access logic here
            # For now, assume user has access if they meet access level
            pass
        
        # Check chapter access
        if file.chapter:
            # Add chapter access logic here
            pass
        
        # Check lesson access
        if file.lesson:
            # Add lesson access logic here
            pass
        
        return True
    
    def log_access_attempt(self, file: File, user, action: str, success: bool, 
                          error_message: str = None, request=None):
        """Log file access attempt for security monitoring"""
        try:
            FileAccessLog.objects.create(
                file=file,
                user=user,
                action=action,
                ip_address=self.get_client_ip(request) if request else '127.0.0.1',
                user_agent=self.get_user_agent(request) if request else 'Unknown',
                referer=self.get_referer(request) if request else None,
                success=success,
                error_message=error_message,
                response_code=200 if success else 403
            )
        except Exception as e:
            logger.error(f"Error logging file access: {e}")
    
    def update_access_count(self, file: File, user, access_type: str):
        """Update access count for rate limiting"""
        try:
            file_access, created = FileAccess.objects.get_or_create(
                file=file,
                user=user,
                access_type=access_type,
                defaults={
                    'granted_by': user,
                    'expires_at': timezone.now() + timedelta(days=30)  # Default 30 days
                }
            )
            
            file_access.access_count += 1
            file_access.last_accessed = timezone.now()
            file_access.save()
            
        except Exception as e:
            logger.error(f"Error updating access count: {e}")
    
    def get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_agent(self, request) -> str:
        """Get user agent from request"""
        return request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    def get_referer(self, request) -> str:
        """Get referer from request"""
        return request.META.get('HTTP_REFERER')
    
    def create_upload_session(self, user, file_name: str, file_size: int, 
                            file_type: str, mime_type: str, request=None) -> FileUploadSession:
        """Create a secure upload session"""
        # Generate upload token
        upload_token = self.generate_upload_token(user, file_name, file_size)
        
        # Create upload session
        session = FileUploadSession.objects.create(
            user=user,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            upload_token=upload_token,
            ip_address=self.get_client_ip(request) if request else '127.0.0.1',
            expires_at=timezone.now() + timedelta(hours=1)  # 1 hour to upload
        )
        
        return session
    
    def generate_upload_token(self, user, file_name: str, file_size: int) -> str:
        """Generate secure upload token"""
        payload = {
            'user_id': str(user.id),
            'file_name': file_name,
            'file_size': file_size,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def verify_upload_token(self, token: str) -> Dict[str, Any]:
        """Verify upload token and return payload"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValidationError("Upload token has expired")
        except jwt.InvalidTokenError:
            raise ValidationError("Invalid upload token")
    
    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def detect_suspicious_activity(self, user, file: File) -> bool:
        """Detect suspicious file access patterns"""
        # Check for too many access attempts in short time
        recent_accesses = FileAccessLog.objects.filter(
            user=user,
            file=file,
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if recent_accesses > 20:  # More than 20 accesses in 5 minutes (was too strict at 10)
            logger.warning(f"Suspicious activity detected for user {user.id} and file {file.id}")
            return True
        
        return False


# Global instance
secure_file_service = SecureFileService()
