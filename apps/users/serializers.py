from rest_framework import serializers
from .models import User, Student, Professor, Admin


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model"""
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'email', 'wilaya', 
            'phone_number', 'academic_stream', 'profile_picture_path',
            'email_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'email_verified', 'created_at', 'updated_at']


class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Student profile"""
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'wilaya', 'phone_number', 
            'academic_stream'
        ]


class StudentProfilePictureSerializer(serializers.ModelSerializer):
    """Serializer for Student profile picture upload"""
    class Meta:
        model = Student
        fields = ['profile_picture_path']


class ProfessorSerializer(serializers.ModelSerializer):
    """Serializer for Professor model"""
    class Meta:
        model = Professor
        fields = [
            'id', 'first_name', 'last_name', 'email', 'wilaya',
            'phone_number', 'academic_stream', 'profile_picture_path',
            'email_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'email_verified', 'created_at', 'updated_at']


class AdminSerializer(serializers.ModelSerializer):
    """Serializer for Admin model"""
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email_verified = serializers.SerializerMethodField()
    # Admin doesn't have these fields, so we'll return None or empty
    wilaya = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    profile_picture_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Admin
        fields = [
            'id', 'first_name', 'last_name', 'email', 'wilaya',
            'phone_number', 'profile_picture_path', 'email_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'email_verified', 'created_at', 'updated_at', 
                           'first_name', 'last_name', 'wilaya', 'phone_number', 'profile_picture_path']
    
    def get_email_verified(self, obj):
        """Admin doesn't have email_verified field, return False by default"""
        # Note: Admin model doesn't have email_verified, but we return False for consistency
        return False
    
    def get_wilaya(self, obj):
        """Admin doesn't have wilaya, return None"""
        return None
    
    def get_phone_number(self, obj):
        """Admin doesn't have phone_number, return None"""
        return None
    
    def get_profile_picture_path(self, obj):
        """Admin doesn't have profile_picture_path, return None"""
        return None
