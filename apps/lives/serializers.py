from rest_framework import serializers
from .models import Live, LiveComment, LiveStatus
from apps.courses.serializers import ModuleSerializer, ChapterSerializer
from apps.courses.models import AcademicStream
from apps.users.models import Professor


class ProfessorSerializer(serializers.ModelSerializer):
    """Simple professor serializer for live sessions"""
    class Meta:
        model = Professor
        fields = ['id', 'first_name', 'last_name', 'email']
    
    email = serializers.SerializerMethodField()
    
    def get_email(self, obj):
        return obj.user.email if obj.user else None


class LiveSerializer(serializers.ModelSerializer):
    """Serializer for live sessions matching frontend structure"""
    professor = ProfessorSerializer(read_only=True)
    professor_id = serializers.UUIDField(write_only=True, required=False)
    module = ModuleSerializer(read_only=True)
    module_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    chapter = ChapterSerializer(read_only=True)
    chapter_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    academic_streams = serializers.SerializerMethodField()
    academic_stream_ids = serializers.ListField(
        child=serializers.UUIDField(),  # Expect UUIDs from frontend
        write_only=True,
        required=False,
        allow_null=True
    )
    
    # Frontend UI fields
    module_name = serializers.CharField(source='module.name', read_only=True)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    professor_name = serializers.SerializerMethodField()
    recording_file = serializers.SerializerMethodField()  # Return ID as string instead of object
    
    class Meta:
        model = Live
        fields = [
            'id', 'title', 'description', 'professor', 'professor_id',
            'module', 'module_id', 'module_name', 'chapter', 'chapter_id', 'chapter_name',
            'academic_streams', 'academic_stream_ids', 'scheduled_datetime',
            'started_at', 'ended_at', 'status', 'recording_url', 'recording_file',
            'jitsi_room_name', 'viewer_count', 'created_at', 'updated_at', 'professor_name'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at', 'viewer_count', 'created_at', 'updated_at']
    
    def get_professor_name(self, obj):
        return f"{obj.professor.first_name} {obj.professor.last_name}" if obj.professor else None
    
    def get_recording_file(self, obj):
        """Return recording_file ID as string or null"""
        return str(obj.recording_file.id) if obj.recording_file else None
    
    def get_academic_streams(self, obj):
        """Return academic streams as a list of strings"""
        return [stream.name for stream in obj.academic_streams.all()]
    
    def create(self, validated_data):
        # Extract foreign key IDs and many-to-many data
        professor_id = validated_data.pop('professor_id', None)
        module_id = validated_data.pop('module_id', None)
        chapter_id = validated_data.pop('chapter_id', None)
        academic_stream_ids = validated_data.pop('academic_stream_ids', [])
        
        # Get professor from request user if not provided
        if not professor_id:
            user = self.context['request'].user
            # Check if user is a professor (admins who also have professor profiles can use it)
            if hasattr(user, 'professor') and user.professor:
                # User has a professor profile - use it (whether they're admin or professor)
                professor = user.professor
            elif hasattr(user, 'admin') and user.admin:
                # Admin without professor profile - create a minimal professor profile for them
                # This allows admins to create lives without needing a separate professor profile
                from apps.users.models import Professor
                from django.utils import timezone
                
                # Check if admin already has a professor profile (double-check)
                if hasattr(user, 'professor') and user.professor:
                    professor = user.professor
                else:
                    # Create a minimal professor profile for the admin
                    # This makes admins work seamlessly as professors
                    # Use user's email/username parts for name if available
                    first_name = user.first_name or (user.email.split('@')[0] if user.email else 'Admin')
                    last_name = user.last_name or 'User'
                    
                    professor, created = Professor.objects.get_or_create(
                        user=user,
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'wilaya': 'Algiers',  # Default wilaya - admin can update later
                            'phone_number': '+213000000000',  # Default phone - admin can update later
                            'gender': 'male',  # Default gender - admin can update later
                            'date_of_birth': timezone.now().date().replace(year=1980),  # Default DOB
                            'status': 'approved',  # Auto-approve admin professors
                            'email_verified': True,
                        }
                    )
            else:
                raise serializers.ValidationError(
                    "You must be a professor or admin to create live sessions."
                )
        else:
            try:
                professor = Professor.objects.get(id=professor_id)
            except Professor.DoesNotExist:
                raise serializers.ValidationError({
                    'professor_id': [f"Professor with id {professor_id} not found"]
                })
        
        # Create the live
        live = Live.objects.create(
            professor=professor,
            module_id=module_id if module_id else None,
            chapter_id=chapter_id if chapter_id else None,
            **validated_data
        )
        
        # Add academic streams using UUIDs (foreign keys)
        if academic_stream_ids:
            stream_objects = []
            for stream_id in academic_stream_ids:
                if not stream_id:
                    continue
                    
                try:
                    stream = AcademicStream.objects.get(id=stream_id)
                    stream_objects.append(stream)
                except AcademicStream.DoesNotExist:
                    # Stream not found - skip this one but don't fail the entire request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Academic stream with id {stream_id} not found")
            
            if stream_objects:
                live.academic_streams.set(stream_objects)
        
        return live
    
    def update(self, instance, validated_data):
        # Handle foreign key updates
        if 'module_id' in validated_data:
            instance.module_id = validated_data.pop('module_id')
        if 'chapter_id' in validated_data:
            instance.chapter_id = validated_data.pop('chapter_id')
        if 'academic_stream_ids' in validated_data:
            academic_stream_ids = validated_data.pop('academic_stream_ids')
            if academic_stream_ids:
                stream_objects = []
                for stream_id in academic_stream_ids:
                    try:
                        stream = AcademicStream.objects.get(id=stream_id)
                        stream_objects.append(stream)
                    except AcademicStream.DoesNotExist:
                        # Stream not found - skip this one
                        continue
                if stream_objects:
                    instance.academic_streams.set(stream_objects)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class LiveListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing lives"""
    module_name = serializers.CharField(source='module.name', read_only=True)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    professor_name = serializers.SerializerMethodField()
    academic_streams = serializers.SerializerMethodField()
    
    class Meta:
        model = Live
        fields = [
            'id', 'title', 'description', 'module_name', 'chapter_name',
            'professor_name', 'academic_streams', 'scheduled_datetime',
            'started_at', 'ended_at', 'status', 'recording_url',
            'viewer_count', 'created_at', 'updated_at'
        ]
    
    def get_professor_name(self, obj):
        return f"{obj.professor.first_name} {obj.professor.last_name}" if obj.professor else None
    
    def get_academic_streams(self, obj):
        return [stream.name for stream in obj.academic_streams.all()]


class LiveCommentSerializer(serializers.ModelSerializer):
    """Serializer for live comments"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveComment
        fields = ['id', 'live', 'user', 'user_name', 'user_email', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        if hasattr(obj.user, 'student'):
            return f"{obj.user.student.first_name} {obj.user.student.last_name}"
        elif hasattr(obj.user, 'professor'):
            return f"{obj.user.professor.first_name} {obj.user.professor.last_name}"
        return obj.user.username
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

