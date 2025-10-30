"""
Serializers for progress tracking
"""
from rest_framework import serializers
from .models import LessonProgress, ChapterProgress, ModuleProgress
from apps.courses.serializers import LessonSerializer, ChapterSerializer, ModuleSerializer


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for LessonProgress model"""
    lesson = LessonSerializer(read_only=True)
    student_name = serializers.CharField(source='student.first_name', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'student_name', 'is_completed', 'is_unlocked',
            'time_spent', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LessonProgressUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating lesson progress"""
    
    class Meta:
        model = LessonProgress
        fields = ['is_completed', 'is_unlocked', 'time_spent']
    
    def update(self, instance, validated_data):
        # Set completed_at when marking as completed
        if validated_data.get('is_completed') and not instance.is_completed:
            from django.utils import timezone
            validated_data['completed_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class ChapterProgressSerializer(serializers.ModelSerializer):
    """Serializer for ChapterProgress model"""
    chapter = ChapterSerializer(read_only=True)
    student_name = serializers.CharField(source='student.first_name', read_only=True)
    
    class Meta:
        model = ChapterProgress
        fields = [
            'id', 'chapter', 'student_name', 'is_completed', 'completion_percentage',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChapterProgressUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating chapter progress"""
    
    class Meta:
        model = ChapterProgress
        fields = ['is_completed', 'completion_percentage']
    
    def update(self, instance, validated_data):
        # Set completed_at when marking as completed
        if validated_data.get('is_completed') and not instance.is_completed:
            from django.utils import timezone
            validated_data['completed_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class ModuleProgressSerializer(serializers.ModelSerializer):
    """Serializer for ModuleProgress model"""
    module = ModuleSerializer(read_only=True)
    student_name = serializers.CharField(source='student.first_name', read_only=True)
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'module', 'student_name', 'is_completed', 'completion_percentage',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleProgressUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating module progress"""
    
    class Meta:
        model = ModuleProgress
        fields = ['is_completed', 'completion_percentage']
    
    def update(self, instance, validated_data):
        # Set completed_at when marking as completed
        if validated_data.get('is_completed') and not instance.is_completed:
            from django.utils import timezone
            validated_data['completed_at'] = timezone.now()
        
        return super().update(instance, validated_data)

