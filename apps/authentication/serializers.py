"""
Authentication serializers for login, registration, and password reset
"""
import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import EmailVerificationToken, PasswordResetToken
from apps.users.models import User, Student, Professor, Admin
from core.email import EmailService


def custom_password_validator(password):
    """Custom password validator that's less strict than Django's default"""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    
    if not any(c.isupper() for c in password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    
    if not any(c.islower() for c in password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    
    if not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least one number.")


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['student', 'professor', 'admin'])
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user_type = attrs.get('user_type')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            # Check user type
            if user_type == 'student' and not hasattr(user, 'student'):
                raise serializers.ValidationError('User is not a student')
            elif user_type == 'professor' and not hasattr(user, 'professor'):
                raise serializers.ValidationError('User is not a professor')
            elif user_type == 'admin' and not hasattr(user, 'admin'):
                raise serializers.ValidationError('User is not an admin')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for student registration"""
    password = serializers.CharField(write_only=True, validators=[custom_password_validator])
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    academic_stream = serializers.CharField()
    
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'wilaya', 'phone_number', 
            'academic_stream', 'email', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('password_confirm')
        email = validated_data.pop('email')
        
        # Create user
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password
        )
        
        # Create student
        student = Student.objects.create(
            user=user,
            **validated_data
        )
        
        return student


class ProfessorRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for professor registration"""
    password = serializers.CharField(write_only=True, validators=[custom_password_validator])
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    cv_file = serializers.FileField(write_only=True, required=True)
    profile_picture = serializers.FileField(write_only=True, required=False)
    
    class Meta:
        model = Professor
        fields = [
            'first_name', 'last_name', 'wilaya', 'phone_number', 'gender',
            'date_of_birth', 'exp_school', 'exp_school_years', 'exp_off_school',
            'exp_online', 'password', 'password_confirm', 'email', 'cv_file', 'profile_picture'
        ]
    
    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters")
        if len(value.strip()) > 50:
            raise serializers.ValidationError("First name must be less than 50 characters")
        if not re.match(r'^[a-zA-Z\u0600-\u06FF\s\'-]+$', value.strip()):
            raise serializers.ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters")
        if len(value.strip()) > 50:
            raise serializers.ValidationError("Last name must be less than 50 characters")
        if not re.match(r'^[a-zA-Z\u0600-\u06FF\s\'-]+$', value.strip()):
            raise serializers.ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes")
        return value.strip()
    
    def validate_phone_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required")
        if not re.match(r'^[\+]?[0-9\-\(\)\s]{10,15}$', value.strip()):
            raise serializers.ValidationError("Please enter a valid phone number (10-15 digits)")
        return value.strip()
    
    def validate_wilaya(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Please select your wilaya")
        return value.strip()
    
    def validate_gender(self, value):
        if not value:
            raise serializers.ValidationError("Please select your gender")
        if value not in ['male', 'female']:
            raise serializers.ValidationError("Gender must be either 'male' or 'female'")
        return value
    
    def validate_date_of_birth(self, value):
        if not value:
            raise serializers.ValidationError("Date of birth is required")
        
        from datetime import date
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 18:
            raise serializers.ValidationError("You must be at least 18 years old to register as a professor")
        if age > 80:
            raise serializers.ValidationError("Please enter a valid date of birth")
        
        return value
    
    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email is required")
        
        # Check if email already exists
        if User.objects.filter(email=value.strip().lower()).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        return value.strip().lower()
    
    def validate_cv_file(self, value):
        if not value:
            raise serializers.ValidationError("CV file is required")
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "CV must be a PDF or Word document (.pdf, .doc, .docx)"
            )
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("CV file size must be less than 10MB")
        
        return value
    
    def validate_profile_picture(self, value):
        if value:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Profile picture must be an image (JPEG, PNG, GIF, or WebP)"
                )
            
            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError("Profile picture size must be less than 5MB")
        
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('password_confirm')
        email = validated_data.pop('email')
        cv_file = validated_data.pop('cv_file')
        profile_picture = validated_data.pop('profile_picture', None)
        
        # Create user
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password
        )
        
        # Handle file uploads to MinIO
        cv_path = None
        profile_picture_path = None
        
        if cv_file:
            cv_path = self._save_file_to_minio(cv_file, 'cv', user.id)
        
        if profile_picture:
            profile_picture_path = self._save_file_to_minio(profile_picture, 'profile_picture', user.id)
        
        # Create professor
        professor = Professor.objects.create(
            user=user,
            cv_path=cv_path,
            profile_picture_path=profile_picture_path,
            **validated_data
        )
        
        return professor
    
    def _save_file_to_minio(self, file, file_type, user_id):
        """Save uploaded file to MinIO and return the file path"""
        import os
        import uuid
        from django.conf import settings
        from minio import Minio
        from minio.error import S3Error
        
        # Generate unique filename
        file_extension = os.path.splitext(file.name)[1]
        filename = f"{file_type}_{user_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Determine storage path based on file type
        if file_type == 'cv':
            storage_path = f"professors/cv/{filename}"
        else:  # profile_picture
            storage_path = f"professors/profile_pictures/{filename}"
        
        try:
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
            
            # Ensure bucket exists
            bucket_name = settings.MINIO_STORAGE_BUCKET_NAME
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
            
            # Upload file to MinIO
            file.seek(0)  # Reset file pointer
            minio_client.put_object(
                bucket_name=bucket_name,
                object_name=storage_path,
                data=file,
                length=file.size,
                content_type=file.content_type
            )
            
            # Return the MinIO URL
            return f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/{storage_path}"
            
        except S3Error as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")
        except Exception as e:
            raise Exception(f"File upload error: {e}")


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['student', 'professor', 'admin'])
    
    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.get(token=value)
            if not token_obj.is_valid():
                raise serializers.ValidationError('Invalid or expired token')
            return value
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError('Invalid token')


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()
    user_type = serializers.ChoiceField(choices=['student', 'professor', 'admin'])
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    password_confirm = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['student', 'professor', 'admin'])
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_token(self, value):
        try:
            token_obj = PasswordResetToken.objects.get(token=value)
            if not token_obj.is_valid():
                raise serializers.ValidationError('Invalid or expired token')
            return value
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Invalid token')


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    refresh_token = serializers.CharField()
