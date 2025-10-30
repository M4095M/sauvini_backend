"""
Views for progress tracking
"""
import uuid
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import LessonProgress, ChapterProgress, ModuleProgress
from .serializers import (
    LessonProgressSerializer, LessonProgressUpdateSerializer,
    ChapterProgressSerializer, ChapterProgressUpdateSerializer,
    ModuleProgressSerializer, ModuleProgressUpdateSerializer
)
from core.permissions import IsStudentUser


# Lesson Progress Views
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_lesson_progress(request, lesson_id):
    """Get progress for a specific lesson"""
    try:
        student = request.user.student
        
        try:
            progress = LessonProgress.objects.get(
                student=student,
                lesson_id=lesson_id
            )
            serializer = LessonProgressSerializer(progress)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Lesson progress retrieved successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except LessonProgress.DoesNotExist:
            # Create progress record if it doesn't exist
            from apps.courses.models import Lesson
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                progress = LessonProgress.objects.create(
                    student=student,
                    lesson=lesson,
                    is_unlocked=True  # Default to unlocked
                )
                serializer = LessonProgressSerializer(progress)
                
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'Lesson progress created and retrieved successfully',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_201_CREATED)
                
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
            'message': f'Error retrieving lesson progress: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStudentUser])
def update_lesson_progress(request, lesson_id):
    """Update progress for a specific lesson"""
    try:
        student = request.user.student
        
        try:
            progress = LessonProgress.objects.get(
                student=student,
                lesson_id=lesson_id
            )
        except LessonProgress.DoesNotExist:
            # Create progress record if it doesn't exist
            from apps.courses.models import Lesson
            try:
                lesson = Lesson.objects.get(id=lesson_id)
                progress = LessonProgress.objects.create(
                    student=student,
                    lesson=lesson,
                    is_unlocked=True
                )
            except Lesson.DoesNotExist:
                return Response({
                    'success': False,
                    'data': None,
                    'message': 'Lesson not found',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = LessonProgressUpdateSerializer(progress, data=request.data, partial=True)
        if serializer.is_valid():
            updated_progress = serializer.save()
            response_serializer = LessonProgressSerializer(updated_progress)
            
            # Update chapter progress when lesson is completed
            if updated_progress.is_completed:
                update_chapter_progress_from_lesson(student, updated_progress.lesson.chapter)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Lesson progress updated successfully',
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
            'message': f'Error updating lesson progress: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_chapter_lesson_progress(request, chapter_id):
    """Get progress for all lessons in a chapter"""
    try:
        student = request.user.student
        
        # Get or create progress for all lessons in the chapter
        from apps.courses.models import Lesson
        lessons = Lesson.objects.filter(chapter_id=chapter_id).order_by('order')
        
        progress_list = []
        for lesson in lessons:
            progress, created = LessonProgress.objects.get_or_create(
                student=student,
                lesson=lesson,
                defaults={'is_unlocked': True}
            )
            progress_list.append(progress)
        
        serializer = LessonProgressSerializer(progress_list, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Chapter lesson progress retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving chapter lesson progress: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Chapter Progress Views
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_chapter_progress(request, chapter_id):
    """Get progress for a specific chapter"""
    try:
        student = request.user.student
        
        try:
            progress = ChapterProgress.objects.get(
                student=student,
                chapter_id=chapter_id
            )
        except ChapterProgress.DoesNotExist:
            # Create progress record if it doesn't exist
            from apps.courses.models import Chapter
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                progress = ChapterProgress.objects.create(
                    student=student,
                    chapter=chapter
                )
            except Chapter.DoesNotExist:
                return Response({
                    'success': False,
                    'data': None,
                    'message': 'Chapter not found',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ChapterProgressSerializer(progress)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Chapter progress retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving chapter progress: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStudentUser])
def update_chapter_progress(request, chapter_id):
    """Update progress for a specific chapter"""
    try:
        student = request.user.student
        
        try:
            progress = ChapterProgress.objects.get(
                student=student,
                chapter_id=chapter_id
            )
        except ChapterProgress.DoesNotExist:
            # Create progress record if it doesn't exist
            from apps.courses.models import Chapter
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                progress = ChapterProgress.objects.create(
                    student=student,
                    chapter=chapter
                )
            except Chapter.DoesNotExist:
                return Response({
                    'success': False,
                    'data': None,
                    'message': 'Chapter not found',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ChapterProgressUpdateSerializer(progress, data=request.data, partial=True)
        if serializer.is_valid():
            updated_progress = serializer.save()
            response_serializer = ChapterProgressSerializer(updated_progress)
            
            # Update module progress when chapter is completed
            if updated_progress.is_completed:
                update_module_progress_from_chapter(student, updated_progress.chapter.module)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Chapter progress updated successfully',
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
            'message': f'Error updating chapter progress: {str(e)}',
            'status': status.HTTP_500_INTERNAL_SERVER_ERROR
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Module Progress Views
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_module_progress(request, module_id):
    """Get progress for a specific module"""
    try:
        student = request.user.student
        
        try:
            progress = ModuleProgress.objects.get(
                student=student,
                module_id=module_id
            )
        except ModuleProgress.DoesNotExist:
            # Create progress record if it doesn't exist
            from apps.courses.models import Module
            try:
                module = Module.objects.get(id=module_id)
                progress = ModuleProgress.objects.create(
                    student=student,
                    module=module
                )
            except Module.DoesNotExist:
                return Response({
                    'success': False,
                    'data': None,
                    'message': 'Module not found',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ModuleProgressSerializer(progress)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Module progress retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving module progress: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_student_progress_summary(request):
    """Get overall progress summary for the student"""
    try:
        student = request.user.student
        
        # Get progress statistics
        lesson_stats = LessonProgress.objects.filter(student=student).aggregate(
            total_lessons=Count('id'),
            completed_lessons=Count('id', filter=Q(is_completed=True)),
            total_time_spent=Avg('time_spent')
        )
        
        chapter_stats = ChapterProgress.objects.filter(student=student).aggregate(
            total_chapters=Count('id'),
            completed_chapters=Count('id', filter=Q(is_completed=True)),
            avg_completion=Avg('completion_percentage')
        )
        
        module_stats = ModuleProgress.objects.filter(student=student).aggregate(
            total_modules=Count('id'),
            completed_modules=Count('id', filter=Q(is_completed=True)),
            avg_completion=Avg('completion_percentage')
        )
        
        summary = {
            'lessons': {
                'total': lesson_stats['total_lessons'] or 0,
                'completed': lesson_stats['completed_lessons'] or 0,
                'completion_rate': round(
                    (lesson_stats['completed_lessons'] or 0) / max(lesson_stats['total_lessons'] or 1, 1) * 100, 2
                ),
                'total_time_spent': lesson_stats['total_time_spent'] or 0
            },
            'chapters': {
                'total': chapter_stats['total_chapters'] or 0,
                'completed': chapter_stats['completed_chapters'] or 0,
                'completion_rate': round(
                    (chapter_stats['completed_chapters'] or 0) / max(chapter_stats['total_chapters'] or 1, 1) * 100, 2
                ),
                'avg_completion': round(chapter_stats['avg_completion'] or 0, 2)
            },
            'modules': {
                'total': module_stats['total_modules'] or 0,
                'completed': module_stats['completed_modules'] or 0,
                'completion_rate': round(
                    (module_stats['completed_modules'] or 0) / max(module_stats['total_modules'] or 1, 1) * 100, 2
                ),
                'avg_completion': round(module_stats['avg_completion'] or 0, 2)
            }
        }
        
        return Response({
            'success': True,
            'data': summary,
            'message': 'Progress summary retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving progress summary: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Helper functions
def update_chapter_progress_from_lesson(student, chapter):
    """Update chapter progress when a lesson is completed"""
    try:
        progress, created = ChapterProgress.objects.get_or_create(
            student=student,
            chapter=chapter
        )
        
        # Calculate completion percentage
        from apps.courses.models import Lesson
        total_lessons = Lesson.objects.filter(chapter=chapter).count()
        completed_lessons = LessonProgress.objects.filter(
            student=student,
            lesson__chapter=chapter,
            is_completed=True
        ).count()
        
        completion_percentage = round((completed_lessons / max(total_lessons, 1)) * 100, 2)
        progress.completion_percentage = completion_percentage
        
        # Mark as completed if all lessons are done
        if completed_lessons == total_lessons and total_lessons > 0:
            progress.is_completed = True
            progress.completed_at = timezone.now()
        
        progress.save()
        
    except Exception as e:
        print(f"Error updating chapter progress: {e}")


def update_module_progress_from_chapter(student, module):
    """Update module progress when a chapter is completed"""
    try:
        progress, created = ModuleProgress.objects.get_or_create(
            student=student,
            module=module
        )
        
        # Calculate completion percentage
        from apps.courses.models import Chapter
        total_chapters = Chapter.objects.filter(module=module).count()
        completed_chapters = ChapterProgress.objects.filter(
            student=student,
            chapter__module=module,
            is_completed=True
        ).count()
        
        completion_percentage = round((completed_chapters / max(total_chapters, 1)) * 100, 2)
        progress.completion_percentage = completion_percentage
        
        # Mark as completed if all chapters are done
        if completed_chapters == total_chapters and total_chapters > 0:
            progress.is_completed = True
            progress.completed_at = timezone.now()
        
        progress.save()
        
    except Exception as e:
        print(f"Error updating module progress: {e}")
