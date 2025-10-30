"""
Secure file management models for LMS
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class FileAccessLevel(models.TextChoices):
    """File access levels for security"""
    PUBLIC = "public", "Public"
    STUDENT = "student", "Student Only"
    PROFESSOR = "professor", "Professor Only"
    ADMIN = "admin", "Admin Only"


class FileType(models.TextChoices):
    """Supported file types"""
    VIDEO = "video", "Video"
    PDF = "pdf", "PDF"
    DOCUMENT = "document", "Document"
    IMAGE = "image", "Image"
    AUDIO = "audio", "Audio"


class File(models.Model):
    """Secure file model with access control"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, unique=True)
    file_type = models.CharField(max_length=20, choices=FileType.choices)
    file_size = models.BigIntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=100)
    
    # Access control
    access_level = models.CharField(
        max_length=20, 
        choices=FileAccessLevel.choices,
        default=FileAccessLevel.STUDENT
    )
    
    # Content relationships
    course = models.ForeignKey('courses.Module', on_delete=models.CASCADE, null=True, blank=True)
    chapter = models.ForeignKey('courses.Chapter', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    
    # Security
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.CharField(max_length=255, null=True, blank=True)
    checksum = models.CharField(max_length=64, null=True, blank=True)  # SHA-256
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Content protection
    allow_download = models.BooleanField(default=True)
    allow_streaming = models.BooleanField(default=True)
    max_downloads = models.IntegerField(null=True, blank=True)  # Rate limiting
    expires_at = models.DateTimeField(null=True, blank=True)  # File expiration
    
    class Meta:
        db_table = 'secure_files'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file_type']),
            models.Index(fields=['access_level']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.file_type})"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_expired(self):
        """Check if file has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class FileAccess(models.Model):
    """Track file access permissions for users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='accesses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_accesses')
    
    # Access details
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('read', 'Read'),
            ('download', 'Download'),
            ('stream', 'Stream'),
            ('edit', 'Edit'),
        ],
        default='read'
    )
    
    # Access control
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='granted_accesses'
    )
    
    # Usage tracking
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'file_accesses'
        unique_together = ['file', 'user', 'access_type']
        indexes = [
            models.Index(fields=['file', 'user']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['granted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.file.name} ({self.access_type})"
    
    @property
    def is_expired(self):
        """Check if access has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class FileAccessLog(models.Model):
    """Log all file access attempts for security monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_access_logs')
    
    # Access details
    action = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('download', 'Download'),
            ('stream', 'Stream'),
            ('upload', 'Upload'),
            ('delete', 'Delete'),
        ]
    )
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referer = models.URLField(null=True, blank=True)
    
    # Result
    success = models.BooleanField()
    error_message = models.TextField(null=True, blank=True)
    response_code = models.IntegerField(null=True, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(null=True, blank=True)  # Request duration
    
    class Meta:
        db_table = 'file_access_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['file', 'user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.user.email} - {self.file.name} ({self.action})"


class FileUploadSession(models.Model):
    """Track file upload sessions for security"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_sessions')
    
    # Upload details
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=20, choices=FileType.choices)
    mime_type = models.CharField(max_length=100)
    
    # Security
    upload_token = models.CharField(max_length=1000, unique=True)
    ip_address = models.GenericIPAddressField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('uploading', 'Uploading'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Result
    uploaded_file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'file_upload_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['upload_token']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.file_name} ({self.status})"
    
    @property
    def is_expired(self):
        """Check if upload session has expired"""
        return timezone.now() > self.expires_at
