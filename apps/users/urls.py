from django.urls import path
from . import views

urlpatterns = [
    # Student profile endpoints
    path('student/profile', views.get_student_profile, name='get_student_profile'),
    path('student/profile/update', views.update_student_profile, name='update_student_profile'),
    path('student/profile/picture', views.upload_student_profile_picture, name='upload_student_profile_picture'),
    path('student/<uuid:student_id>', views.get_student_by_id, name='get_student_by_id'),
    
    # Professor profile endpoints
    path('professor/profile', views.get_professor_profile, name='get_professor_profile'),
    
    # Admin profile endpoints
    path('admin/profile', views.get_admin_profile, name='get_admin_profile'),
]


