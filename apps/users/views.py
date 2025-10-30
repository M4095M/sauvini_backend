"""
User views for student, professor, and admin management
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os

from .models import User, Student, Professor, Admin
from .serializers import (
    StudentSerializer, StudentUpdateSerializer, StudentProfilePictureSerializer,
    ProfessorSerializer, AdminSerializer
)
from core.permissions import IsStudentUser, IsProfessorUser, IsAdminUser


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStudentUser])
def get_student_profile(request):
    """Get current student's profile"""
    try:
        student = request.user.student
        serializer = StudentSerializer(student)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_by_id(request, student_id):
    """Get student by ID (public endpoint)"""
    try:
        student = get_object_or_404(Student, id=student_id)
        serializer = StudentSerializer(student)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStudentUser])
def update_student_profile(request):
    """Update current student's profile"""
    try:
        student = request.user.student
        serializer = StudentUpdateSerializer(student, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # Return updated profile
            updated_serializer = StudentSerializer(student)
            return Response({
                'success': True,
                'data': updated_serializer.data
            })
        else:
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStudentUser])
def upload_student_profile_picture(request):
    """Upload student profile picture"""
    try:
        student = request.user.student
        
        if 'profile_picture' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No profile picture file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        profile_picture = request.FILES['profile_picture']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return Response({
                'success': False,
                'error': 'Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            return Response({
                'success': False,
                'error': 'File size too large. Maximum size is 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique filename
        file_extension = os.path.splitext(profile_picture.name)[1]
        filename = f"student_profile_{student.id}_{uuid.uuid4().hex}{file_extension}"
        
        # Save file
        file_path = default_storage.save(f"profile_pictures/{filename}", ContentFile(profile_picture.read()))
        
        # Update student profile picture path
        student.profile_picture_path = default_storage.url(file_path)
        student.save()
        
        # Return updated profile
        serializer = StudentSerializer(student)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Student profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfessorUser])
def get_professor_profile(request):
    """Get current professor's profile"""
    try:
        professor = request.user.professor
        serializer = ProfessorSerializer(professor)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Professor.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Professor profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_admin_profile(request):
    """Get current admin's profile"""
    try:
        admin = request.user.admin
        serializer = AdminSerializer(admin)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Admin.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Admin profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)