"""
Notification models
"""
from django.db import models
from django.utils import timezone
import uuid


class Notification(models.Model):
    """Notification model matching Rust Notification struct"""
    NOTIFICATION_TYPES = [
        ('purchase_approved', 'Purchase Approved'),
        ('purchase_rejected', 'Purchase Rejected'),
        ('professor_approved', 'Professor Approved'),
        ('professor_rejected', 'Professor Rejected'),
        ('lesson_available', 'Lesson Available'),
        ('quiz_reminder', 'Quiz Reminder'),
        ('general', 'General'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"