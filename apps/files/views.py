"""
Secure file API views
"""
import os
import uuid
import hashlib
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

from .models import File, FileAccess, FileAccessLog, FileUploadSession, FileAccessLevel, FileType
from .services import secure_file_service
from .serializers import FileSerializer, FileAccessSerializer, FileUploadSessionSerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_file_access(request, file_id):
    """
    Get secure access URL for a file
    
    GET /api/v1/files/{file_id}/access
    """
    try:
        file = File.objects.get(id=file_id, is_active=True)
    except File.DoesNotExist:
        return Response({
            'success': False,
            'message': 'File not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Suspicious activity detection disabled for now
    # if secure_file_service.detect_suspicious_activity(request.user, file):
    #     return Response({
    #         'success': False,
    #         'message': 'Access temporarily restricted due to suspicious activity',
    #         'request_id': str(uuid.uuid4()),
    #         'timestamp': timezone.now().isoformat()
    #     }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    try:
        # Determine access type based on file type
        access_type = 'stream' if file.file_type == FileType.VIDEO else 'download'
        
        # Generate signed URL
        signed_url = secure_file_service.generate_signed_url(
            file=file,
            user=request.user,
            access_type=access_type,
            expires_in=3600  # 1 hour
        )
        
        return Response({
            'success': True,
            'data': {
                'file_id': str(file.id),
                'file_name': file.name,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'signed_url': signed_url,
                'expires_in': 3600,
                'access_type': access_type
            },
            'message': 'File access granted',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating file access for {file_id}: {e}")
        return Response({
            'success': False,
            'message': f'Error generating file access: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_upload_session(request):
    """
    Create a secure upload session
    
    POST /api/v1/files/upload/session
    Body: {
        "file_name": "example.pdf",
        "file_size": 1024000,
        "file_type": "pdf",
        "mime_type": "application/pdf",
        "access_level": "student",
        "course_id": "uuid",
        "chapter_id": "uuid",
        "lesson_id": "uuid"
    }
    """
    try:
        # Validate required fields
        required_fields = ['file_name', 'file_size', 'file_type', 'mime_type']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'success': False,
                    'message': f'Missing required field: {field}',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        if request.data['file_type'] not in [choice[0] for choice in FileType.choices]:
            return Response({
                'success': False,
                'message': 'Invalid file type',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate access level
        access_level = request.data.get('access_level', 'student')
        if access_level not in [choice[0] for choice in FileAccessLevel.choices]:
            return Response({
                'success': False,
                'message': 'Invalid access level',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file size limits
        max_size_mb = 100  # 100MB default limit
        file_size_mb = request.data['file_size'] / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return Response({
                'success': False,
                'message': f'File size exceeds maximum allowed size of {max_size_mb}MB',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create upload session
        session = secure_file_service.create_upload_session(
            user=request.user,
            file_name=request.data['file_name'],
            file_size=request.data['file_size'],
            file_type=request.data['file_type'],
            mime_type=request.data['mime_type'],
            request=request
        )
        
        # Generate upload URL
        upload_url = f"/api/v1/files/upload/{session.upload_token}"
        
        return Response({
            'success': True,
            'data': {
                'upload_session_id': str(session.id),
                'upload_token': session.upload_token,
                'upload_url': upload_url,
                'expires_at': session.expires_at.isoformat(),
                'max_file_size': request.data['file_size']
            },
            'message': 'Upload session created successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating upload session: {e}")
        return Response({
            'success': False,
            'message': f'Error creating upload session: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request, upload_token):
    """
    Upload file using secure token
    
    POST /api/v1/files/upload/{upload_token}
    """
    try:
        # Verify upload token
        token_payload = secure_file_service.verify_upload_token(upload_token)
        
        # Get upload session
        try:
            session = FileUploadSession.objects.get(
                upload_token=upload_token,
                user=request.user,
                status__in=['pending', 'uploading']
            )
        except FileUploadSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired upload session',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if session has expired
        if session.is_expired:
            session.status = 'cancelled'
            session.save()
            return Response({
                'success': False,
                'message': 'Upload session has expired',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_410_GONE)
        
        # Update session status
        session.status = 'uploading'
        session.save()
        
        # Get uploaded file
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'message': 'No file provided',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file
        if uploaded_file.size != session.file_size:
            session.status = 'failed'
            session.error_message = 'File size mismatch'
            session.save()
            return Response({
                'success': False,
                'message': 'File size does not match expected size',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate secure file path
        file_extension = os.path.splitext(session.file_name)[1]
        secure_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"protected/{session.file_type}s/{secure_filename}"
        
        # Upload to MinIO
        try:
            # Reset file pointer to beginning for upload
            uploaded_file.seek(0)
            secure_file_service.minio_client.put_object(
                bucket_name=secure_file_service.bucket_name,
                object_name=file_path,
                data=uploaded_file,
                length=uploaded_file.size,
                content_type=session.mime_type
            )
        except Exception as e:
            session.status = 'failed'
            session.error_message = str(e)
            session.save()
            logger.error(f"Error uploading file to MinIO: {e}")
            return Response({
                'success': False,
                'message': 'Error uploading file to storage',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Calculate file checksum
        # Reset file pointer to beginning for checksum calculation
        uploaded_file.seek(0)
        file_content = uploaded_file.read()
        checksum = hashlib.sha256(file_content).hexdigest()
        uploaded_file.seek(0)  # Reset for potential future use
        
        # Create file record
        file_obj = File.objects.create(
            name=session.file_name,
            original_name=session.file_name,
            file_path=file_path,
            file_type=session.file_type,
            file_size=session.file_size,
            mime_type=session.mime_type,
            access_level=request.data.get('access_level', 'student'),
            course_id=request.data.get('course_id'),
            chapter_id=request.data.get('chapter_id'),
            lesson_id=request.data.get('lesson_id'),
            uploaded_by=request.user,
            checksum=checksum
        )
        
        # Update session
        session.status = 'completed'
        session.uploaded_file = file_obj
        session.completed_at = timezone.now()
        session.save()
        
        return Response({
            'success': True,
            'data': {
                'file_id': str(file_obj.id),
                'file_name': file_obj.name,
                'file_type': file_obj.file_type,
                'file_size': file_obj.file_size,
                'access_level': file_obj.access_level,
                'checksum': file_obj.checksum
            },
            'message': 'File uploaded successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except ValidationError as e:
        return Response({
            'success': False,
            'message': str(e),
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return Response({
            'success': False,
            'message': f'Error uploading file: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_files(request):
    """
    List files uploaded by the user
    
    GET /api/v1/files/my-files
    """
    try:
        files = File.objects.filter(
            uploaded_by=request.user,
            is_active=True
        ).order_by('-created_at')
        
        serializer = FileSerializer(files, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Files retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing user files: {e}")
        return Response({
            'success': False,
            'message': f'Error retrieving files: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    """
    Delete a file (soft delete)
    
    DELETE /api/v1/files/{file_id}
    """
    try:
        file = File.objects.get(id=file_id, uploaded_by=request.user)
        
        # Soft delete
        file.is_active = False
        file.save()
        
        return Response({
            'success': True,
            'message': 'File deleted successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except File.DoesNotExist:
        return Response({
            'success': False,
            'message': 'File not found or access denied',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        return Response({
            'success': False,
            'message': f'Error deleting file: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
