"""
Custom DRF permissions for role-based access control
"""
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Permission for admin users only"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'admin') and 
            request.user.admin is not None
        )


class IsProfessorUser(BasePermission):
    """Permission for professor users only"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'professor') and 
            request.user.professor is not None
        )


class IsStudentUser(BasePermission):
    """Permission for student users only"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'student') and 
            request.user.student is not None
        )


class IsAdminOrProfessor(BasePermission):
    """Permission for admin or professor users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (
                (hasattr(request.user, 'admin') and request.user.admin is not None) or
                (hasattr(request.user, 'professor') and request.user.professor is not None)
            )
        )


class IsAdminOrStudent(BasePermission):
    """Permission for admin or student users"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (
                (hasattr(request.user, 'admin') and request.user.admin is not None) or
                (hasattr(request.user, 'student') and request.user.student is not None)
            )
        )
