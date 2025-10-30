"""
User models for Student, Professor, and Admin
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Base user model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email


class Student(models.Model):
    """Student model matching Rust Student struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    wilaya = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    academic_stream = models.CharField(max_length=100)
    profile_picture_path = models.URLField(max_length=500, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Professor(models.Model):
    """Professor model matching Rust Professor struct"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('deactivated', 'Deactivated'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    wilaya = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateTimeField()
    exp_school = models.BooleanField(default=False)
    exp_school_years = models.IntegerField(null=True, blank=True)
    exp_off_school = models.BooleanField(default=False)
    exp_online = models.BooleanField(default=False)
    cv_path = models.URLField(max_length=500, blank=True, null=True)
    profile_picture_path = models.URLField(max_length=500, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'professors'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Admin(models.Model):
    """Admin model matching Rust Admin struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admins'
    
    def __str__(self):
        return f"Admin: {self.user.email}"