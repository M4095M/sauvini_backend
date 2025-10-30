"""
Views for courses app
"""
import uuid
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Module, Chapter, Lesson, AcademicStream, ModuleEnrollment
from .serializers import ModuleSerializer, ChapterSerializer, LessonSerializer, AcademicStreamSerializer, ModuleEnrollmentSerializer, ModuleEnrollmentCreateSerializer
from core.permissions import IsStudentUser


@api_view(['GET'])
@permission_classes([AllowAny])
def get_modules(request):
    """Get all modules"""
    try:
        modules = Module.objects.all().order_by('name')
        serializer = ModuleSerializer(modules, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Modules retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving modules: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_module_by_id(request, module_id):
    """Get a specific module by ID"""
    try:
        module = Module.objects.get(id=module_id)
        serializer = ModuleSerializer(module)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Module retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Module.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Module not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving module: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_chapters_by_module(request, module_id):
    """Get all chapters for a specific module"""
    try:
        chapters = Chapter.objects.filter(module_id=module_id).prefetch_related('academic_streams').order_by('name')
        serializer = ChapterSerializer(chapters, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Chapters retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving chapters: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_chapter_by_id(request, chapter_id):
    """Get a specific chapter by ID"""
    try:
        chapter = Chapter.objects.prefetch_related('academic_streams').get(id=chapter_id)
        serializer = ChapterSerializer(chapter)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Chapter retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Chapter.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Chapter not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving chapter: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_chapter(request, chapter_id):
    """Update a specific chapter by ID with comprehensive data"""
    try:
        # Debug: Print received data
        print(f"Received data for chapter {chapter_id}: {request.data}")
        
        chapter = Chapter.objects.get(id=chapter_id)
        
        # Update basic chapter fields
        if 'name' in request.data:
            chapter.name = request.data['name']
        if 'description' in request.data:
            chapter.description = request.data['description']
        if 'price' in request.data:
            chapter.price = request.data['price']
        
        # Update academic streams if provided
        if 'academic_streams' in request.data:
            stream_ids = request.data['academic_streams']
            print(f"Processing academic streams: {stream_ids}")
            # Clear existing streams and add new ones
            chapter.academic_streams.clear()
            for stream_id in stream_ids:
                try:
                    stream = AcademicStream.objects.get(id=stream_id)
                    chapter.academic_streams.add(stream)
                    print(f"Added stream {stream_id} to chapter")
                except AcademicStream.DoesNotExist:
                    print(f"Stream {stream_id} not found, skipping")
                    # Skip invalid stream IDs
                    continue
        else:
            print("No academic_streams in request data")
        
        # Save all changes to database
        chapter.save()
        
        serializer = ChapterSerializer(chapter)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Chapter updated successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Chapter.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Chapter not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error updating chapter: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_stream_to_chapter(request, chapter_id, stream_id):
    """Add an academic stream to a chapter"""
    try:
        chapter = Chapter.objects.get(id=chapter_id)
        stream = AcademicStream.objects.get(id=stream_id)
        
        # Add the stream to the chapter
        chapter.academic_streams.add(stream)
        
        return Response({
            'success': True,
            'data': {'success': True},
            'message': 'Academic stream added to chapter successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Chapter.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Chapter not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
        
    except AcademicStream.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Academic stream not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error adding stream to chapter: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_lessons_by_chapter(request, chapter_id):
    """Get all lessons for a specific chapter"""
    try:
        lessons = Lesson.objects.filter(chapter_id=chapter_id).order_by('order')
        serializer = LessonSerializer(lessons, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Lessons retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving lessons: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def create_lesson(request):
    """Create a new lesson"""
    try:
        # Get the chapter
        chapter_id = request.data.get('chapter_id')
        if not chapter_id:
            return Response({
                'success': False,
                'data': None,
                'message': 'Chapter ID is required',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            chapter = Chapter.objects.get(id=chapter_id)
        except Chapter.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'message': 'Chapter not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare lesson data
        lesson_data = {
            'title': request.data.get('title', ''),
            'description': request.data.get('description', ''),
            'image': request.data.get('image'),
            'duration': request.data.get('duration', 30),
            'order': request.data.get('order', 1),
            'video_url': request.data.get('video_url'),
            'pdf_url': request.data.get('pdf_url'),
            'exercise_total_mark': request.data.get('exercise_total_mark', 0),
            'exercise_total_xp': request.data.get('exercise_total_xp', 0),
            'chapter': chapter.id
        }
        
        # Validate required fields
        if not lesson_data['title']:
            return Response({
                'success': False,
                'data': None,
                'message': 'Lesson title is required',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not lesson_data['description']:
            return Response({
                'success': False,
                'data': None,
                'message': 'Lesson description is required',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the lesson
        serializer = LessonSerializer(data=lesson_data)
        if serializer.is_valid():
            lesson = serializer.save()
            
            # Handle academic streams if provided
            academic_streams = request.data.get('academic_streams', [])
            if academic_streams:
                try:
                    stream_objects = AcademicStream.objects.filter(id__in=academic_streams)
                    lesson.academic_streams.set(stream_objects)
                except Exception as e:
                    print(f"Warning: Could not process academic streams: {e}")
            
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Lesson created successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'data': None,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error creating lesson: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_lesson_by_id(request, lesson_id):
    """Get a specific lesson by ID with optional progress data"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        serializer = LessonSerializer(lesson)
        lesson_data = serializer.data
        
        # Add progress data if user is authenticated as a student
        if request.user.is_authenticated and hasattr(request.user, 'student'):
            from apps.progress.models import LessonProgress
            try:
                progress = LessonProgress.objects.get(
                    student=request.user.student,
                    lesson=lesson
                )
                lesson_data['progress'] = {
                    'is_completed': progress.is_completed,
                    'is_unlocked': progress.is_unlocked,
                    'time_spent': progress.time_spent,
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                }
            except LessonProgress.DoesNotExist:
                # Default progress for new lesson
                lesson_data['progress'] = {
                    'is_completed': False,
                    'is_unlocked': True,
                    'time_spent': 0,
                    'completed_at': None,
                }
        else:
            # Default progress for unauthenticated users
            lesson_data['progress'] = {
                'is_completed': False,
                'is_unlocked': True,
                'time_spent': 0,
                'completed_at': None,
            }
        
        return Response({
            'success': True,
            'data': lesson_data,
            'message': 'Lesson retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Lesson.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Lesson not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving lesson: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def update_lesson(request, lesson_id):
    """Update an existing lesson"""
    try:
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'message': 'Lesson not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare update data
        update_data = {}
        
        if 'title' in request.data:
            update_data['title'] = request.data['title']
        if 'description' in request.data:
            update_data['description'] = request.data['description']
        if 'image' in request.data:
            update_data['image'] = request.data['image']
        if 'duration' in request.data:
            update_data['duration'] = request.data['duration']
        if 'order' in request.data:
            update_data['order'] = request.data['order']
        if 'video_url' in request.data:
            update_data['video_url'] = request.data['video_url']
        if 'pdf_url' in request.data:
            update_data['pdf_url'] = request.data['pdf_url']
        if 'exercise_total_mark' in request.data:
            update_data['exercise_total_mark'] = request.data['exercise_total_mark']
        if 'exercise_total_xp' in request.data:
            update_data['exercise_total_xp'] = request.data['exercise_total_xp']
        
        # Validate required fields if provided
        if 'title' in update_data and not update_data['title']:
            return Response({
                'success': False,
                'data': None,
                'message': 'Lesson title cannot be empty',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'description' in update_data and not update_data['description']:
            return Response({
                'success': False,
                'data': None,
                'message': 'Lesson description cannot be empty',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the lesson
        serializer = LessonSerializer(lesson, data=update_data, partial=True)
        if serializer.is_valid():
            updated_lesson = serializer.save()
            
            # Handle academic streams if provided
            if 'academic_streams' in request.data:
                academic_streams = request.data.get('academic_streams', [])
                try:
                    stream_objects = AcademicStream.objects.filter(id__in=academic_streams)
                    updated_lesson.academic_streams.set(stream_objects)
                except Exception as e:
                    print(f"Warning: Could not update academic streams: {e}")
            
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Lesson updated successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'data': None,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error updating lesson: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  # Temporarily allow any for testing
def delete_lesson(request, lesson_id):
    """Delete a lesson"""
    try:
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'message': 'Lesson not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        lesson.delete()
        
        return Response({
            'success': True,
            'data': None,
            'message': 'Lesson deleted successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error deleting lesson: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_academic_streams(request):
    """Get all academic streams"""
    try:
        streams = AcademicStream.objects.all().order_by('name')
        serializer = AcademicStreamSerializer(streams, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Academic streams retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving academic streams: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Enrollment Views
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentUser])
def enroll_in_module(request, module_id):
    """Enroll student in a module"""
    try:
        # Get the module
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'message': 'Module not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create enrollment
        serializer = ModuleEnrollmentCreateSerializer(
            data={'module': module_id},
            context={'request': request}
        )
        
        if serializer.is_valid():
            enrollment = serializer.save()
            response_serializer = ModuleEnrollmentSerializer(enrollment)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Successfully enrolled in module',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'data': None,
                'message': f'Enrollment failed: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error enrolling in module: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStudentUser])
def unenroll_from_module(request, module_id):
    """Unenroll student from a module"""
    try:
        student = request.user.student
        
        try:
            enrollment = ModuleEnrollment.objects.get(
                student=student,
                module_id=module_id,
                is_active=True
            )
        except ModuleEnrollment.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'message': 'Student is not enrolled in this module',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Deactivate enrollment instead of deleting
        enrollment.is_active = False
        enrollment.save()
        
        return Response({
            'success': True,
            'data': None,
            'message': 'Successfully unenrolled from module',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error unenrolling from module: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_enrolled_modules(request):
    """Get all modules the student is enrolled in"""
    try:
        student = request.user.student
        enrollments = ModuleEnrollment.objects.filter(
            student=student,
            is_active=True
        ).select_related('module').order_by('-enrolled_at')
        
        serializer = ModuleEnrollmentSerializer(enrollments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Enrolled modules retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving enrolled modules: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def check_enrollment_status(request, module_id):
    """Check if student is enrolled in a specific module"""
    try:
        student = request.user.student
        
        is_enrolled = ModuleEnrollment.objects.filter(
            student=student,
            module_id=module_id,
            is_active=True
        ).exists()
        
        return Response({
            'success': True,
            'data': {
                'is_enrolled': is_enrolled,
                'module_id': module_id
            },
            'message': 'Enrollment status retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error checking enrollment status: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)