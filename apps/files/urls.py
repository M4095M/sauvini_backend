"""
URL patterns for secure file management
"""
from django.urls import path
from . import views

urlpatterns = [
    # File access
    path('files/<uuid:file_id>/access', views.get_file_access, name='get_file_access'),
    
    # File upload
    path('files/upload/session', views.create_upload_session, name='create_upload_session'),
    path('files/upload/<str:upload_token>', views.upload_file, name='upload_file'),
    
    # File management
    path('files/my-files', views.list_user_files, name='list_user_files'),
    path('files/<uuid:file_id>', views.delete_file, name='delete_file'),
]
