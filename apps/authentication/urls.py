"""
Authentication URL patterns matching Rust backend exactly
"""
from django.urls import path
from . import views
from . import health_views

urlpatterns = [
    # Health check routes (no authentication required)
    path('health', health_views.health_check, name='health_check'),
    path('health/live', health_views.liveness, name='liveness'),
    
    # Public auth routes (no authentication required)
    path('auth/admin/login', views.admin_login, name='admin_login'),
    path('auth/admin/forgot-password', views.send_password_reset_email, name='admin_forgot_password'),
    path('auth/admin/reset-password', views.reset_password, name='admin_reset_password'),
    path('auth/admin/refresh-token', views.refresh_token, name='admin_refresh_token'),
    
    path('auth/professor/login', views.professor_login, name='professor_login'),
    path('auth/professor/register', views.professor_register, name='professor_register'),
    path('auth/professor/send-verification-email', views.send_verification_email, name='professor_send_verification'),
    path('auth/professor/verify-email', views.verify_email, name='professor_verify_email'),
    path('auth/professor/forgot-password', views.send_password_reset_email, name='professor_forgot_password'),
    path('auth/professor/reset-password', views.reset_password, name='professor_reset_password'),
    path('auth/professor/refresh-token', views.refresh_token, name='professor_refresh_token'),
    
    path('auth/student/register', views.student_register, name='student_register'),
    path('auth/student/login', views.student_login, name='student_login'),
    path('auth/student/send-verification-email', views.send_verification_email, name='student_send_verification'),
    path('auth/student/verify-email', views.verify_email, name='student_verify_email'),
    path('auth/student/forgot-password', views.send_password_reset_email, name='student_forgot_password'),
    path('auth/student/reset-password', views.reset_password, name='student_reset_password'),
    path('auth/student/refresh-token', views.refresh_token, name='student_refresh_token'),
    
    # Protected admin routes (require authentication)
    path('auth/admin/approve-professor', views.approve_professor, name='approve_professor'),
    path('auth/admin/reject-professor', views.reject_professor, name='reject_professor'),
    path('auth/admin/all-professors', views.get_all_professors, name='get_all_professors'),
    path('auth/admin/students', views.get_all_students, name='get_all_students'),
    path('auth/admin/students/<str:student_id>', views.get_student_by_id, name='get_student_by_id'),
    
    # Professor CV download routes (require authentication)
    path('auth/professor/<str:professor_id>/cv/download', views.download_professor_cv, name='download_professor_cv'),
    path('auth/professor/<str:professor_id>/cv/url', views.get_professor_cv_url, name='get_professor_cv_url'),
    
    # Logout routes (require authentication)
    path('auth/logout', views.logout, name='logout'),
    path('auth/logout-all-devices', views.logout_all_devices, name='logout_all_devices'),
]
