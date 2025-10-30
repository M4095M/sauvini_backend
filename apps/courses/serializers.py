"""
Serializers for courses app
"""
from rest_framework import serializers
from .models import Module, Chapter, Lesson, AcademicStream, ModuleEnrollment


class AcademicStreamSerializer(serializers.ModelSerializer):
    """Serializer for AcademicStream model"""
    
    class Meta:
        model = AcademicStream
        fields = ['id', 'name', 'name_ar']


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module model"""
    academic_streams = AcademicStreamSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = [
            'id', 'custom_id', 'name', 'description', 'image_path', 
            'color', 'academic_streams', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChapterSerializer(serializers.ModelSerializer):
    """Serializer for Chapter model"""
    academic_streams = AcademicStreamSerializer(many=True, read_only=True)
    
    class Meta:
        model = Chapter
        fields = [
            'id', 'name', 'description', 'price', 'module', 'academic_streams'
        ]
        read_only_fields = ['id']


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model"""
    academic_streams = serializers.SerializerMethodField()
    stream_ids = serializers.SerializerMethodField()
    chapter_id = serializers.SerializerMethodField()
    video_file_id = serializers.SerializerMethodField()
    pdf_file_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'image', 'duration', 'order',
            'video_url', 'pdf_url', 'video_file_id', 'pdf_file_id',
            'exercise_total_mark', 'exercise_total_xp',
            'academic_streams', 'stream_ids', 'chapter', 'chapter_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_academic_streams(self, obj):
        """Return academic streams as objects with id and name"""
        return [
            {
                'id': str(stream.id),
                'name': stream.name,
                'labelKey': stream.name  # For frontend compatibility
            }
            for stream in obj.academic_streams.all()
        ]
    
    def get_stream_ids(self, obj):
        """Return academic stream IDs as array"""
        return [str(stream.id) for stream in obj.academic_streams.all()]
    
    def get_chapter_id(self, obj):
        """Return chapter ID as string"""
        return str(obj.chapter.id) if obj.chapter else None
    
    def get_video_file_id(self, obj):
        """Return video file ID (UUID) for secure access"""
        if obj.video_file:
            return str(obj.video_file.id)
        # Try to extract UUID from URL if it's a full file URL
        if obj.video_url:
            # Check if URL contains a UUID pattern
            import re
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            match = re.search(uuid_pattern, obj.video_url, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def get_pdf_file_id(self, obj):
        """Return PDF file ID (UUID) for secure access"""
        if obj.pdf_file:
            return str(obj.pdf_file.id)
        # Try to extract UUID from URL if it's a full file URL
        if obj.pdf_url:
            # Check if URL contains a UUID pattern
            import re
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            match = re.search(uuid_pattern, obj.pdf_url, re.IGNORECASE)
            if match:
                return match.group(0)
        return None


class ModuleEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for ModuleEnrollment model"""
    module = ModuleSerializer(read_only=True)
    student_name = serializers.CharField(source='student.first_name', read_only=True)
    
    class Meta:
        model = ModuleEnrollment
        fields = [
            'id', 'module', 'student_name', 'enrolled_at', 'is_active'
        ]
        read_only_fields = ['id', 'enrolled_at']


class ModuleEnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating module enrollments"""
    
    class Meta:
        model = ModuleEnrollment
        fields = ['module']
    
    def create(self, validated_data):
        student = self.context['request'].user.student
        module = validated_data['module']
        
        # Check if already enrolled
        if ModuleEnrollment.objects.filter(student=student, module=module).exists():
            raise serializers.ValidationError("Student is already enrolled in this module")
        
        return ModuleEnrollment.objects.create(
            student=student,
            module=module
        )
