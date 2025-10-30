"""
Live streaming models
"""
from django.db import models
from django.utils import timezone
import uuid


class LiveStatus(models.TextChoices):
    """Live status choices matching frontend enum"""
    PENDING = 'Pending', 'Pending'  # Scheduled, awaiting admin approval
    APPROVED = 'Approved', 'Approved'  # Approved by admin, waiting to start
    LIVE = 'Live', 'Live'  # Currently active
    ENDED = 'Ended', 'Ended'  # Has ended
    CANCELLED = 'Cancelled', 'Cancelled'  # Cancelled before start


class Live(models.Model):
    """Live streaming session model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    professor = models.ForeignKey('users.Professor', on_delete=models.CASCADE, related_name='lives')
    module = models.ForeignKey('courses.Module', on_delete=models.SET_NULL, null=True, blank=True, related_name='lives')
    chapter = models.ForeignKey('courses.Chapter', on_delete=models.SET_NULL, null=True, blank=True, related_name='lives')
    academic_streams = models.ManyToManyField('courses.AcademicStream', related_name='lives', blank=True)
    scheduled_datetime = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LiveStatus.choices, default=LiveStatus.PENDING)
    recording_url = models.URLField(max_length=500, blank=True, null=True)
    recording_file = models.ForeignKey('files.File', on_delete=models.SET_NULL, null=True, blank=True, related_name='live_recordings')
    jitsi_room_name = models.CharField(max_length=200, blank=True, null=True, help_text="Jitsi Meet room name for this live session")
    viewer_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lives'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.professor.first_name} {self.professor.last_name}"


class LiveComment(models.Model):
    """Comments/chat for live sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live = models.ForeignKey(Live, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='live_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'live_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.live.title}"

