"""
Views for lives app
"""
import uuid
import logging
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Live, LiveComment, LiveStatus
from .serializers import LiveSerializer, LiveListSerializer, LiveCommentSerializer
from core.permissions import IsProfessorUser, IsAdminOrProfessor

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrProfessor])
def lives_list_create(request):
    """List all lives or create a new live"""
    # Both admins and professors can create lives
    # For admins, they can specify a professor_id in the request
    # For professors, the professor is automatically set to the logged-in professor
    
    if request.method == 'GET':
        try:
            # Get query parameters
            status_filter = request.query_params.get('status')
            academic_stream = request.query_params.get('academic_stream')
            module_id = request.query_params.get('module_id')
            chapter_id = request.query_params.get('chapter_id')
            page = int(request.query_params.get('page', 1))
            per_page = int(request.query_params.get('per_page', 20))
            
            # Start with base queryset
            queryset = Live.objects.select_related(
                'professor', 'module', 'chapter'
            ).prefetch_related('academic_streams')
            
            # Apply filters
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            if module_id:
                queryset = queryset.filter(module_id=module_id)
            
            if chapter_id:
                queryset = queryset.filter(chapter_id=chapter_id)
            
            if academic_stream:
                # Filter by academic stream name (case-insensitive)
                queryset = queryset.filter(academic_streams__name__iexact=academic_stream).distinct()
            
            # If user is professor, only show their lives
            if hasattr(request.user, 'professor') and request.user.professor:
                queryset = queryset.filter(professor=request.user.professor)
            
            # Order by creation date
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            start = (page - 1) * per_page
            end = start + per_page
            total = queryset.count()
            lives = queryset[start:end]
            
            serializer = LiveListSerializer(lives, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'lives': serializer.data,
                    'total': total,
                    'page': page,
                    'per_page': per_page
                },
                'message': 'Lives retrieved successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'Error retrieving lives: {str(e)}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        try:
            # Handle academic_streams field from frontend (backward compatibility)
            # Frontend now sends academic_stream_ids directly, but we still support academic_streams
            data = request.data.copy()
            if 'academic_streams' in data and 'academic_stream_ids' not in data:
                data['academic_stream_ids'] = data.pop('academic_streams')
            
            serializer = LiveSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                live = serializer.save()
                response_serializer = LiveSerializer(live)
                return Response({
                    'success': True,
                    'data': {'live': response_serializer.data},
                    'message': 'Live session created successfully. Waiting for admin approval.',
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
        except serializers.ValidationError as e:
            # Validation errors should return 400
            # Extract meaningful error messages from ValidationError
            error_message = "Validation error"
            if hasattr(e, 'detail'):
                if isinstance(e.detail, dict):
                    # Field-specific errors
                    error_list = []
                    for field, messages in e.detail.items():
                        if isinstance(messages, list):
                            error_list.extend([str(msg) for msg in messages])
                        else:
                            error_list.append(str(messages))
                    error_message = "; ".join(error_list) if error_list else str(e.detail)
                elif isinstance(e.detail, list):
                    error_message = "; ".join([str(msg) for msg in e.detail])
                else:
                    error_message = str(e.detail)
            else:
                error_message = str(e)
            
            return Response({
                'success': False,
                'data': None,
                'message': error_message,
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'Error creating live: {str(e)}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminOrProfessor])
def live_detail(request, live_id):
    """Get, update, or delete a specific live"""
    try:
        live = get_object_or_404(Live, id=live_id)
        
        # Check if professor owns this live or is admin
        if hasattr(request.user, 'professor') and request.user.professor:
            if live.professor != request.user.professor:
                return Response({
                    'success': False,
                    'data': None,
                    'message': 'You do not have permission to access this live session',
                    'request_id': str(uuid.uuid4()),
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_403_FORBIDDEN)
    except Live.DoesNotExist:
        return Response({
            'success': False,
            'data': None,
            'message': 'Live session not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = LiveSerializer(live)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Live retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = LiveSerializer(live, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Live updated successfully',
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
    
    elif request.method == 'DELETE':
        live.delete()
        return Response({
            'success': True,
            'data': None,
            'message': 'Live deleted successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsProfessorUser])
def cancel_live(request, live_id):
    """Cancel a live session"""
    try:
        live = get_object_or_404(Live, id=live_id)
        
        # Check ownership
        if live.professor != request.user.professor:
            return Response({
                'success': False,
                'data': None,
                'message': 'You do not have permission to cancel this live session',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Can only cancel if not already ended or cancelled
        if live.status == LiveStatus.ENDED:
            return Response({
                'success': False,
                'data': None,
                'message': 'Cannot cancel a live that has already ended',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if live.status == LiveStatus.CANCELLED:
            return Response({
                'success': False,
                'data': None,
                'message': 'Live is already cancelled',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        live.status = LiveStatus.CANCELLED
        live.save()
        
        serializer = LiveSerializer(live)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Live cancelled successfully. Admin and students will be notified.',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error cancelling live: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsProfessorUser])
def start_live(request, live_id):
    """Start a live session"""
    try:
        live = get_object_or_404(Live, id=live_id)
        
        # Check ownership
        if live.professor != request.user.professor:
            return Response({
                'success': False,
                'data': None,
                'message': 'You do not have permission to start this live session',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Can only start if approved or pending (and scheduled time has passed)
        if live.status not in [LiveStatus.PENDING, LiveStatus.APPROVED]:
            return Response({
                'success': False,
                'data': None,
                'message': f'Cannot start live with status: {live.status}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate Jitsi room name if not already set
        if not live.jitsi_room_name:
            # Create a unique room name using live ID (remove hyphens for URL-friendly name)
            room_name = f"sauvini-live-{str(live.id).replace('-', '')}"
            live.jitsi_room_name = room_name
        
        live.status = LiveStatus.LIVE
        live.started_at = timezone.now()
        live.save()
        
        serializer = LiveSerializer(live)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Live started successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error starting live: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsProfessorUser])
def end_live(request, live_id):
    """End a live session"""
    try:
        live = get_object_or_404(Live, id=live_id)
        
        # Check ownership
        if live.professor != request.user.professor:
            return Response({
                'success': False,
                'data': None,
                'message': 'You do not have permission to end this live session',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Can only end if currently live
        if live.status != LiveStatus.LIVE:
            return Response({
                'success': False,
                'data': None,
                'message': f'Cannot end live with status: {live.status}. Live must be active.',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        live.status = LiveStatus.ENDED
        live.ended_at = timezone.now()
        
        # Handle recording file upload if provided
        if 'recording' in request.FILES:
            from .services import upload_recording_from_file_object
            recording_file = request.FILES['recording']
            file_obj = upload_recording_from_file_object(live, recording_file)
            if not file_obj:
                logger.error(f"Failed to upload recording for live {live.id}")
        else:
            # No file uploaded, but recording might be available from Jibri
            # In this case, a background task or management command should process it
            logger.info(f"Live {live.id} ended without recording file upload. Recording may be processed later.")
        
        live.save()
        
        serializer = LiveSerializer(live)
        return Response({
            'success': True,
            'data': {
                'live': serializer.data,
                'recording_url': live.recording_url
            },
            'message': 'Live ended successfully. It will be saved under recorded lives.',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error ending live: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def live_comments(request, live_id):
    """Get comments for a live or add a comment"""
    try:
        live = get_object_or_404(Live, id=live_id)
        
        if request.method == 'GET':
            comments = LiveComment.objects.filter(live=live).select_related('user').order_by('created_at')
            serializer = LiveCommentSerializer(comments, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Comments retrieved successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            serializer = LiveCommentSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                comment = serializer.save(live=live)
                response_serializer = LiveCommentSerializer(comment)
                return Response({
                    'success': True,
                    'data': response_serializer.data,
                    'message': 'Comment added successfully',
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
            'message': f'Error with comments: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

