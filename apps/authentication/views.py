"""
Authentication views for login, registration, and password reset
"""
import uuid
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from .serializers import (
    LoginSerializer, StudentRegistrationSerializer, ProfessorRegistrationSerializer,
    EmailVerificationSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    RefreshTokenSerializer
)

# Custom token serializer to include user role in JWT claims
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = str(user.id)
        token['email'] = user.email
        
        # Determine user role based on related models
        if hasattr(user, 'admin'):
            token['role'] = 'admin'
        elif hasattr(user, 'professor'):
            token['role'] = 'professor'
        elif hasattr(user, 'student'):
            token['role'] = 'student'
        else:
            token['role'] = 'user'
            
        return token
from .models import EmailVerificationToken, PasswordResetToken
from core.email import EmailService
from core.permissions import IsAdminUser, IsProfessorUser, IsStudentUser
from apps.users.models import Student, Professor, Admin
from django.http import HttpResponse, Http404
from django.conf import settings
from minio import Minio
from minio.error import S3Error
import os

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for user with custom claims"""
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims to both access and refresh tokens
    refresh['user_id'] = str(user.id)
    refresh['email'] = user.email
    
    # Determine user role based on related models
    if hasattr(user, 'admin'):
        role = 'admin'
    elif hasattr(user, 'professor'):
        role = 'professor'
    elif hasattr(user, 'student'):
        role = 'student'
    else:
        role = 'user'
    
    refresh['role'] = role
    
    # Get access token from refresh token
    access_token = refresh.access_token
    access_token['user_id'] = str(user.id)
    access_token['email'] = user.email
    access_token['role'] = role
    
    return {
        'access': str(access_token),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def student_register(request):
    """Student registration endpoint matching Rust StudentHandler::register_student"""
    serializer = StudentRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        student = serializer.save()
        
        # Update user email
        student.user.email = request.data.get('email', student.user.email)
        student.user.save()
        
        # Note: Verification email will be sent by the frontend OTP component
        # to avoid duplicate emails
        
        return Response({
            'success': True,
            'data': {
                'id': str(student.id),
                'first_name': student.first_name,
                'last_name': student.last_name,
                'wilaya': student.wilaya,
                'phone_number': student.phone_number,
                'academic_stream': student.academic_stream,
                'email': student.user.email,
                'email_verified': student.email_verified,
                'created_at': student.created_at.isoformat(),
                'updated_at': student.updated_at.isoformat()
            },
            'message': 'Student registered successfully. Please proceed to verify your email.',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def professor_register(request):
    """Professor registration endpoint matching Rust ProfessorHandler::register_professor"""
    import json
    
    try:
        # Handle FormData from frontend
        if 'professor_data' in request.data:
            # Parse the JSON string from FormData
            professor_data = json.loads(request.data['professor_data'])
        else:
            # Fallback to direct data (for testing)
            professor_data = request.data
        
        # Add email to the data if it exists
        if 'email' in request.data:
            professor_data['email'] = request.data['email']
        
        # Add file data to the professor_data
        if 'cv_file' in request.FILES:
            professor_data['cv_file'] = request.FILES['cv_file']
        
        if 'profile_picture' in request.FILES:
            professor_data['profile_picture'] = request.FILES['profile_picture']
        
        # Debug: Print the received data
        print(f"Professor registration data received: {professor_data}")
        print(f"Files received: CV={bool(request.FILES.get('cv_file'))}, Profile={bool(request.FILES.get('profile_picture'))}")
        
        serializer = ProfessorRegistrationSerializer(data=professor_data)
        if serializer.is_valid():
            professor = serializer.save()
            
            # Update user email
            professor.user.email = professor_data.get('email', professor.user.email)
            professor.user.save()
            
            # Mark professor as email verified (no email verification required for professors)
            professor.email_verified = True
            professor.save()
            
            # Note: No email verification for professors - only for students
            # Professors are automatically verified upon registration
            
            return Response({
                'success': True,
                'message': 'Professor registered successfully. You can now log in.',
                'data': {
                    'professor_id': str(professor.id),
                    'first_name': professor.first_name,
                    'last_name': professor.last_name,
                    'email': professor.user.email,
                    'email_verified': professor.email_verified,
                    'cv_path': professor.cv_path,
                    'profile_picture_path': professor.profile_picture_path,
                    'created_at': professor.created_at.isoformat(),
                    'updated_at': professor.updated_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
        
        # Debug: Print validation errors
        print(f"Professor registration validation errors: {serializer.errors}")
        
        # Return structured error response
        return Response({
            'success': False,
            'message': 'Registration failed. Please check the errors below.',
            'errors': serializer.errors,
            'field_errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except json.JSONDecodeError as e:
        return Response({
            'success': False,
            'message': 'Invalid JSON data received.',
            'errors': {'professor_data': ['Invalid JSON format']}
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print(f"Unexpected error in professor registration: {str(e)}")
        return Response({
            'success': False,
            'message': 'An unexpected error occurred. Please try again.',
            'errors': {'general': ['An unexpected error occurred. Please try again.']}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def student_login(request):
    """Student login endpoint matching Rust StudentHandler::login_student"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Check if email is verified
        if not user.student.email_verified:
            return Response({
                'success': False,
                'data': {
                    'user': {
                        'id': str(user.student.id),
                        'first_name': user.student.first_name,
                        'last_name': user.student.last_name,
                        'email': user.email,
                        'email_verified': False,
                    }
                },
                'message': 'Email not verified. Please check your email and verify your account.',
                'requires_verification': True,
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Email is verified, proceed with normal login
        tokens = get_tokens_for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'token': {
                    'access_token': tokens['access'],
                    'refresh_token': tokens['refresh'],
                },
                'user': {
                    'id': str(user.student.id),
                    'first_name': user.student.first_name,
                    'last_name': user.student.last_name,
                    'email': user.email,
                    'email_verified': user.student.email_verified,
                }
            },
            'message': 'Login successful',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def professor_login(request):
    """Professor login endpoint matching Rust ProfessorHandler::login_professor"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'token': {
                    'access_token': tokens['access'],
                    'refresh_token': tokens['refresh'],
                },
                'user': {
                    'id': str(user.professor.id),
                    'first_name': user.professor.first_name,
                    'last_name': user.professor.last_name,
                    'email': user.email,
                    'email_verified': user.professor.email_verified,
                    'status': user.professor.status,
                }
            },
            'message': 'Login successful',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """Admin login endpoint matching Rust AdminHandler::login_admin"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'token': {
                    'access_token': tokens['access'],
                    'refresh_token': tokens['refresh'],
                },
                'user': {
                    'id': str(user.admin.id),
                    'email': user.email,
                }
            },
            'message': 'Login successful',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_email(request):
    """Send verification email endpoint"""
    email = request.data.get('email')
    user_type = request.data.get('user_type', 'student')
    
    # Add logging to debug the issue
    print(f"🔍 send_verification_email called with:")
    print(f"   Email: {email}")
    print(f"   User type: {user_type}")
    print(f"   Request data: {request.data}")
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        print(f"   User found: {user.email}")
        
        # Get user name based on user type
        if user_type == 'student' and hasattr(user, 'student'):
            user_name = f"{user.student.first_name} {user.student.last_name}"
        elif user_type == 'professor' and hasattr(user, 'professor'):
            user_name = f"{user.professor.first_name} {user.professor.last_name}"
        else:
            user_name = user.email.split('@')[0]  # Fallback to email prefix
        
        token_obj = EmailVerificationToken.create_token(user, user_type)
        print(f"   Token created: {token_obj.token}")
        print(f"   User name: {user_name}")
        
        try:
            result = EmailService.send_verification_email(user.email, token_obj.token, user_name, user_type)
            print(f"   Email service result: {result}")
        except ValueError as e:
            # Email configuration error - this is a server misconfiguration
            print(f"   ❌ Email configuration error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Email service is not properly configured. Please contact support.',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Other email sending errors
            print(f"   ❌ Error sending email: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Failed to send verification email. Please try again later.',
                'message': 'An error occurred while sending the email.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'Verification email sent successfully'
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        print(f"   User not found: {email}")
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'An unexpected error occurred. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    """Email verification endpoint matching Rust handlers"""
    token = request.GET.get('token')
    user_type = request.GET.get('type', 'student')
    
    serializer = EmailVerificationSerializer(data={'token': token, 'user_type': user_type})
    if serializer.is_valid():
        token_obj = EmailVerificationToken.objects.get(token=token)
        token_obj.is_used = True
        token_obj.save()
        
        # Mark email as verified
        user = token_obj.user
        if user_type == 'student' and hasattr(user, 'student'):
            user.student.email_verified = True
            user.student.save()
        elif user_type == 'professor' and hasattr(user, 'professor'):
            user.professor.email_verified = True
            user.professor.save()
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_password_reset_email(request):
    """Send password reset email endpoint"""
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user_type = serializer.validated_data['user_type']
        
        user = User.objects.get(email=email)
        token_obj = PasswordResetToken.create_token(user, user_type)
        EmailService.send_password_reset_email(user.email, token_obj.token, user_type)
        
        return Response({
            'message': 'Password reset email sent successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Password reset confirmation endpoint"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        token_obj = PasswordResetToken.objects.get(token=token)
        token_obj.is_used = True
        token_obj.save()
        
        # Update password
        user = token_obj.user
        user.set_password(password)
        user.save()
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Token refresh endpoint"""
    serializer = RefreshTokenSerializer(data=request.data)
    if serializer.is_valid():
        try:
            refresh = RefreshToken(serializer.validated_data['refresh_token'])
            
            # Get user from the refresh token payload
            user_id = refresh.payload.get('user_id')
            if not user_id:
                return Response({
                    'error': 'Invalid refresh token: missing user_id'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user from database
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new tokens with custom claims
            new_refresh = RefreshToken.for_user(user)
            new_refresh['user_id'] = str(user.id)
            new_refresh['email'] = user.email
            
            # Determine user role
            if hasattr(user, 'admin'):
                role = 'admin'
            elif hasattr(user, 'professor'):
                role = 'professor'
            elif hasattr(user, 'student'):
                role = 'student'
            else:
                role = 'user'
            
            new_refresh['role'] = role
            
            # Get access token and add custom claims
            access_token = new_refresh.access_token
            access_token['user_id'] = str(user.id)
            access_token['email'] = user.email
            access_token['role'] = role
            
            # Blacklist the old refresh token
            refresh.blacklist()
            
            return Response({
                'success': True,
                'data': {
                    'token': {
                        'access_token': str(access_token),
                        'refresh_token': str(new_refresh),
                    }
                },
                'message': 'Token refreshed successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response({
                'error': f'Invalid refresh token: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Token refresh failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin-only endpoints
@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_professor(request):
    """Approve professor endpoint matching Rust AdminHandler::approve_professor"""
    professor_id = request.data.get('professor_id') or request.data.get('id')
    try:
        professor = Professor.objects.get(id=professor_id)
        professor.status = 'approved'
        professor.save()
        
        # Send approval email
        EmailService.send_professor_approval_email(professor.user.email, True)
        
        return Response({
            'message': 'Professor approved successfully'
        }, status=status.HTTP_200_OK)
    except Professor.DoesNotExist:
        return Response({
            'error': 'Professor not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_professor(request):
    """Reject professor endpoint matching Rust AdminHandler::reject_professor"""
    professor_id = request.data.get('professor_id') or request.data.get('id')
    try:
        professor = Professor.objects.get(id=professor_id)
        professor.status = 'rejected'
        professor.save()
        
        # Send rejection email
        EmailService.send_professor_approval_email(professor.user.email, False)
        
        return Response({
            'message': 'Professor rejected successfully'
        }, status=status.HTTP_200_OK)
    except Professor.DoesNotExist:
        return Response({
            'error': 'Professor not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_professors(request):
    """Get all professors endpoint matching Rust AdminHandler::get_all_professors"""
    professors = Professor.objects.all()
    data = []
    for professor in professors:
        data.append({
            'id': str(professor.id),
            'first_name': professor.first_name,
            'last_name': professor.last_name,
            'email': professor.user.email,
            'phone_number': professor.phone_number,
            'wilaya': professor.wilaya,
            'gender': professor.gender,
            'date_of_birth': professor.date_of_birth.isoformat(),
            'exp_school': professor.exp_school,
            'exp_school_years': professor.exp_school_years,
            'exp_off_school': professor.exp_off_school,
            'exp_online': professor.exp_online,
            'cv_path': professor.cv_path,
            'profile_picture_path': professor.profile_picture_path,
            'email_verified': professor.email_verified,
            'status': professor.status,
            'created_at': professor.created_at.isoformat(),
            'updated_at': professor.updated_at.isoformat(),
        })
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_students(request):
    """Get all students endpoint for admin management with pagination and filtering"""
    from django.core.paginator import Paginator
    from apps.users.models import Student
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    search = request.GET.get('search', '')
    wilaya = request.GET.get('wilaya', '')
    academic_stream = request.GET.get('academic_stream', '')
    email_verified = request.GET.get('email_verified', '')
    
    # Start with all students
    students = Student.objects.select_related('user').all()
    
    # Apply filters
    if search:
        students = students.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(user__email__icontains=search)
        )
    
    if wilaya:
        students = students.filter(wilaya__icontains=wilaya)
    
    if academic_stream:
        students = students.filter(academic_stream__icontains=academic_stream)
    
    if email_verified:
        students = students.filter(email_verified=email_verified.lower() == 'true')
    
    # Order by creation date (newest first)
    students = students.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(students, per_page)
    page_obj = paginator.get_page(page)
    
    # Build response data
    data = []
    for student in page_obj:
        data.append({
            'id': str(student.id),
            'first_name': student.first_name,
            'last_name': student.last_name,
            'email': student.user.email,
            'phone_number': student.phone_number,
            'wilaya': student.wilaya,
            'academic_stream': student.academic_stream,
            'profile_picture_path': student.profile_picture_path,
            'email_verified': student.email_verified,
            'created_at': student.created_at.isoformat(),
            'updated_at': student.updated_at.isoformat(),
        })
    
    # Return paginated response matching frontend expectations
    return Response({
        'success': True,
        'data': {
            'students': data,
            'total': paginator.count,
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
        'message': 'Students retrieved successfully',
        'request_id': str(uuid.uuid4()),
        'timestamp': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_student_by_id(request, student_id):
    """Get individual student details by ID for admin management"""
    from apps.users.models import Student
    
    try:
        # Get student with related user data
        student = Student.objects.select_related('user').get(id=student_id)
        
        # Build response data
        data = {
            'id': str(student.id),
            'first_name': student.first_name,
            'last_name': student.last_name,
            'email': student.user.email,
            'phone_number': student.phone_number,
            'wilaya': student.wilaya,
            'academic_stream': student.academic_stream,
            'profile_picture_path': student.profile_picture_path,
            'email_verified': student.email_verified,
            'created_at': student.created_at.isoformat(),
            'updated_at': student.updated_at.isoformat(),
        }
        
        return Response({
            'success': True,
            'data': data,
            'message': 'Student retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Student.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Student not found',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving student: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout endpoint to blacklist refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Blacklist the refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Logout successful',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except TokenError as e:
        return Response({
            'error': f'Invalid token: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Logout failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_all_devices(request):
    """Logout from all devices by blacklisting all user's tokens"""
    try:
        user = request.user
        
        # Get all outstanding tokens for the user
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        tokens = OutstandingToken.objects.filter(user=user)
        
        # Blacklist all tokens
        for token in tokens:
            try:
                refresh_token = RefreshToken(token.token)
                refresh_token.blacklist()
            except TokenError:
                # Token might already be blacklisted or invalid
                continue
        
        return Response({
            'success': True,
            'message': 'Logged out from all devices',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Logout all devices failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_professor_cv(request, professor_id):
    """Download professor CV file from MinIO"""
    try:
        # Get professor
        professor = Professor.objects.get(id=professor_id)
        
        # Check permissions - only admin, the professor themselves, or approved professors can access
        user = request.user
        if not (hasattr(user, 'admin') or 
                (hasattr(user, 'professor') and user.professor.id == professor.id) or
                (hasattr(user, 'professor') and user.professor.status == 'approved')):
            return Response({
                'error': 'You do not have permission to access this CV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not professor.cv_path:
            return Response({
                'error': 'CV not found for this professor'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize MinIO client
        endpoint_url = settings.MINIO_ENDPOINT_URL
        if endpoint_url.startswith('http://'):
            endpoint = endpoint_url.replace('http://', '')
            secure = False
        elif endpoint_url.startswith('https://'):
            endpoint = endpoint_url.replace('https://', '')
            secure = True
        else:
            endpoint = endpoint_url
            secure = settings.MINIO_USE_HTTPS
        
        minio_client = Minio(
            endpoint=endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )
        
        # Extract object name from the stored path
        # Path format: http://localhost:9000/sauvini/professors/cv/filename.pdf
        bucket_name = settings.MINIO_STORAGE_BUCKET_NAME
        if professor.cv_path.startswith(settings.MINIO_ENDPOINT_URL):
            object_name = professor.cv_path.replace(f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/", "")
        else:
            # Fallback: assume it's just the object name
            object_name = professor.cv_path
        
        # Get file from MinIO
        try:
            response = minio_client.get_object(bucket_name, object_name)
            file_data = response.read()
            response.close()
            response.release_conn()
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return Response({
                    'error': 'CV file not found in storage'
                }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                    'error': f'Error retrieving CV: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Determine content type and filename
        file_extension = os.path.splitext(object_name)[1].lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        # Generate filename
        filename = f"{professor.first_name}_{professor.last_name}_CV{file_extension}"
        
        # Return file as HTTP response
        response = HttpResponse(file_data, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(file_data)
        
        return response
        
    except Professor.DoesNotExist:
        return Response({
            'error': 'Professor not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error downloading CV: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_professor_cv_url(request, professor_id):
    """Get signed URL for professor CV download"""
    try:
        # Get professor
        professor = Professor.objects.get(id=professor_id)
        
        # Check permissions
        user = request.user
        if not (hasattr(user, 'admin') or 
                (hasattr(user, 'professor') and user.professor.id == professor.id) or
                (hasattr(user, 'professor') and user.professor.status == 'approved')):
            return Response({
                'error': 'You do not have permission to access this CV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not professor.cv_path:
            return Response({
                'error': 'CV not found for this professor'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize MinIO client
        endpoint_url = settings.MINIO_ENDPOINT_URL
        if endpoint_url.startswith('http://'):
            endpoint = endpoint_url.replace('http://', '')
            secure = False
        elif endpoint_url.startswith('https://'):
            endpoint = endpoint_url.replace('https://', '')
            secure = True
        else:
            endpoint = endpoint_url
            secure = settings.MINIO_USE_HTTPS
        
        minio_client = Minio(
            endpoint=endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )
        
        # Extract object name from the stored path
        bucket_name = settings.MINIO_STORAGE_BUCKET_NAME
        if professor.cv_path.startswith(settings.MINIO_ENDPOINT_URL):
            object_name = professor.cv_path.replace(f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/", "")
        else:
            object_name = professor.cv_path
        
        # Generate signed URL (valid for 1 hour)
        from datetime import timedelta
        signed_url = minio_client.presigned_get_object(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=timedelta(hours=1)
        )
        
        return Response({
            'success': True,
            'data': {
                'professor_id': str(professor.id),
                'professor_name': f"{professor.first_name} {professor.last_name}",
                'cv_url': signed_url,
                'expires_in': 3600  # 1 hour in seconds
            },
            'message': 'CV access URL generated successfully'
        }, status=status.HTTP_200_OK)
        
    except Professor.DoesNotExist:
        return Response({
            'error': 'Professor not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error generating CV URL: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)