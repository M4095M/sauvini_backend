"""
Admin configuration for secure file management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import File, FileAccess, FileAccessLog, FileUploadSession


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'file_type', 'file_size_mb', 'access_level', 'uploaded_by',
        'created_at', 'is_active', 'download_count'
    ]
    list_filter = ['file_type', 'access_level', 'is_active', 'created_at']
    search_fields = ['name', 'original_name', 'uploaded_by__email']
    readonly_fields = ['id', 'file_path', 'checksum', 'created_at', 'updated_at']
    raw_id_fields = ['uploaded_by', 'course', 'chapter', 'lesson']
    
    fieldsets = (
        ('File Information', {
            'fields': ('id', 'name', 'original_name', 'file_path', 'file_type', 'file_size', 'mime_type')
        }),
        ('Access Control', {
            'fields': ('access_level', 'allow_download', 'allow_streaming', 'max_downloads', 'expires_at')
        }),
        ('Content Association', {
            'fields': ('course', 'chapter', 'lesson'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('is_encrypted', 'encryption_key', 'checksum'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def download_count(self, obj):
        """Show total download count"""
        return FileAccess.objects.filter(file=obj, access_type='download').aggregate(
            total=models.Sum('access_count')
        )['total'] or 0
    download_count.short_description = 'Downloads'


@admin.register(FileAccess)
class FileAccessAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'file_name', 'access_type', 'granted_at', 'expires_at',
        'access_count', 'is_expired'
    ]
    list_filter = ['access_type', 'granted_at', 'expires_at']
    search_fields = ['user__email', 'file__name']
    raw_id_fields = ['file', 'user', 'granted_by']
    
    def file_name(self, obj):
        """Show file name"""
        return obj.file.name
    file_name.short_description = 'File Name'
    
    def is_expired(self, obj):
        """Show if access has expired"""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired.short_description = 'Status'


@admin.register(FileAccessLog)
class FileAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'file_name', 'action', 'ip_address', 'success',
        'response_code', 'timestamp'
    ]
    list_filter = ['action', 'success', 'timestamp', 'response_code']
    search_fields = ['user__email', 'file__name', 'ip_address']
    raw_id_fields = ['file', 'user']
    readonly_fields = ['timestamp']
    
    def file_name(self, obj):
        """Show file name"""
        return obj.file.name
    file_name.short_description = 'File Name'
    
    def success_status(self, obj):
        """Show success status with color"""
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    success_status.short_description = 'Status'


@admin.register(FileUploadSession)
class FileUploadSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'file_name', 'file_type', 'file_size_mb', 'status',
        'created_at', 'expires_at', 'is_expired'
    ]
    list_filter = ['file_type', 'status', 'created_at']
    search_fields = ['user__email', 'file_name']
    raw_id_fields = ['user', 'uploaded_file']
    readonly_fields = ['id', 'upload_token', 'created_at', 'completed_at']
    
    def file_size_mb(self, obj):
        """Show file size in MB"""
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'Size (MB)'
    
    def is_expired(self, obj):
        """Show if session has expired"""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired.short_description = 'Status'
