"""
Course models for Module, Chapter, Lesson, and AcademicStream
"""
from django.db import models
from django.utils import timezone
import uuid


class AcademicStream(models.Model):
    """AcademicStream model matching Rust AcademicStream struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'academic_streams'
    
    def __str__(self):
        return self.name


class Module(models.Model):
    """Module model matching Rust Module struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    custom_id = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    image_path = models.URLField(max_length=500, blank=True, null=True)
    color = models.CharField(max_length=7)  # Hex color code
    academic_streams = models.ManyToManyField(AcademicStream, related_name='modules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'modules'
    
    def __str__(self):
        return self.name


class Chapter(models.Model):
    """Chapter model matching Rust Chapter struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='chapters')
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price in DZD
    academic_streams = models.ManyToManyField(AcademicStream, related_name='chapters', blank=True)
    
    class Meta:
        db_table = 'chapters'
    
    def __str__(self):
        return f"{self.module.name} - {self.name}"


class Lesson(models.Model):
    """Lesson model matching Rust Lesson struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.URLField(max_length=500, blank=True, null=True)  # Lesson thumbnail URL
    duration = models.IntegerField()  # Duration in minutes
    order = models.IntegerField()  # Display order within chapter
    video_url = models.URLField(max_length=500, blank=True, null=True)  # Video lesson URL (legacy, for backwards compatibility)
    pdf_url = models.URLField(max_length=500, blank=True, null=True)  # PDF content URL (legacy, for backwards compatibility)
    video_file = models.ForeignKey('files.File', on_delete=models.SET_NULL, null=True, blank=True, related_name='video_lessons')  # Video file reference
    pdf_file = models.ForeignKey('files.File', on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_lessons')  # PDF file reference
    exercise_total_mark = models.IntegerField(default=0)  # Total marks for exercises
    exercise_total_xp = models.IntegerField(default=0)  # Total XP for exercises
    academic_streams = models.ManyToManyField(AcademicStream, related_name='lessons', blank=True)  # Academic streams this lesson targets
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lessons'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.chapter.name} - {self.title}"


class ModuleEnrollment(models.Model):
    """Module enrollment model for student-module relationships"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='module_enrollments')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'module_enrollments'
        unique_together = ['student', 'module']
    
    def __str__(self):
        return f"{self.student.first_name} - {self.module.name}"