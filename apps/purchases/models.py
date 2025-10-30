"""
Purchase models for chapter purchases
"""
from django.db import models
from django.utils import timezone
import uuid


class Purchase(models.Model):
    """Purchase model matching Rust Purchase struct"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='purchases')
    chapter = models.ForeignKey('courses.Chapter', on_delete=models.CASCADE, related_name='purchases')
    module = models.ForeignKey('courses.Module', on_delete=models.CASCADE, related_name='purchases')
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price in DZD
    phone = models.CharField(max_length=20)  # Payment phone number
    receipt_url = models.URLField(max_length=500)  # Receipt image URL
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey('users.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_purchases')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchases'
        unique_together = ['student', 'chapter']
    
    def __str__(self):
        return f"{self.student} - {self.chapter.name} ({self.status})"