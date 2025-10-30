"""
Progress models for student progress tracking
"""
from django.db import models
from django.utils import timezone
import uuid


class LessonProgress(models.Model):
    """Lesson progress model matching Rust LessonProgress struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    is_unlocked = models.BooleanField(default=False)
    time_spent = models.IntegerField(default=0)  # Time spent in minutes
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lesson_progress'
        unique_together = ['student', 'lesson']
    
    def __str__(self):
        return f"{self.student} - {self.lesson.title} ({'Completed' if self.is_completed else 'In Progress'})"


class ChapterProgress(models.Model):
    """Chapter progress model for tracking overall chapter completion"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='chapter_progress')
    chapter = models.ForeignKey('courses.Chapter', on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0)  # 0-100
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chapter_progress'
        unique_together = ['student', 'chapter']
    
    def __str__(self):
        return f"{self.student} - {self.chapter.name} ({self.completion_percentage}%)"


class ModuleProgress(models.Model):
    """Module progress model for tracking overall module completion"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='module_progress')
    module = models.ForeignKey('courses.Module', on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0)  # 0-100
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'module_progress'
        unique_together = ['student', 'module']
    
    def __str__(self):
        return f"{self.student} - {self.module.name} ({self.completion_percentage}%)"