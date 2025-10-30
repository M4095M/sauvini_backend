"""
Serializers for secure file management
"""
from rest_framework import serializers
from .models import File, FileAccess, FileAccessLog, FileUploadSession, FileAccessLevel, FileType


class FileSerializer(serializers.ModelSerializer):
    """Serializer for File model"""
    file_size_mb = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = File
        fields = [
            'id', 'name', 'original_name', 'file_type', 'file_size', 'file_size_mb',
            'mime_type', 'access_level', 'course', 'chapter', 'lesson',
            'is_encrypted', 'checksum', 'uploaded_by', 'created_at', 'updated_at',
            'is_active', 'allow_download', 'allow_streaming', 'max_downloads',
            'expires_at', 'is_expired'
        ]
        read_only_fields = [
            'id', 'file_path', 'checksum', 'uploaded_by', 'created_at', 'updated_at'
        ]


class FileAccessSerializer(serializers.ModelSerializer):
    """Serializer for FileAccess model"""
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = FileAccess
        fields = [
            'id', 'file', 'user', 'access_type', 'granted_at', 'expires_at',
            'granted_by', 'access_count', 'last_accessed', 'is_expired'
        ]
        read_only_fields = ['id', 'granted_at', 'access_count', 'last_accessed']


class FileAccessLogSerializer(serializers.ModelSerializer):
    """Serializer for FileAccessLog model"""
    
    class Meta:
        model = FileAccessLog
        fields = [
            'id', 'file', 'user', 'action', 'ip_address', 'user_agent',
            'referer', 'success', 'error_message', 'response_code',
            'timestamp', 'duration_ms'
        ]
        read_only_fields = ['id', 'timestamp']


class FileUploadSessionSerializer(serializers.ModelSerializer):
    """Serializer for FileUploadSession model"""
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = FileUploadSession
        fields = [
            'id', 'user', 'file_name', 'file_size', 'file_type', 'mime_type',
            'upload_token', 'ip_address', 'status', 'created_at', 'expires_at',
            'completed_at', 'uploaded_file', 'error_message', 'is_expired'
        ]
        read_only_fields = [
            'id', 'upload_token', 'ip_address', 'created_at', 'completed_at'
        ]


class CreateUploadSessionSerializer(serializers.Serializer):
    """Serializer for creating upload sessions"""
    file_name = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField(min_value=1)
    file_type = serializers.ChoiceField(choices=FileType.choices)
    mime_type = serializers.CharField(max_length=100)
    access_level = serializers.ChoiceField(
        choices=FileAccessLevel.choices,
        default=FileAccessLevel.STUDENT
    )
    course_id = serializers.UUIDField(required=False, allow_null=True)
    chapter_id = serializers.UUIDField(required=False, allow_null=True)
    lesson_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_file_size(self, value):
        """Validate file size"""
        max_size_mb = 100  # 100MB limit
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if value > max_size_bytes:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size_mb}MB"
            )
        
        return value
    
    def validate_file_type(self, value):
        """Validate file type"""
        allowed_types = ['video', 'pdf', 'document', 'image', 'audio']
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"File type must be one of: {', '.join(allowed_types)}"
            )
        
        return value


class FileAccessRequestSerializer(serializers.Serializer):
    """Serializer for requesting file access"""
    access_type = serializers.ChoiceField(
        choices=['read', 'download', 'stream'],
        default='read'
    )
    expires_in = serializers.IntegerField(
        min_value=300,  # 5 minutes
        max_value=86400,  # 24 hours
        default=3600  # 1 hour
    )
