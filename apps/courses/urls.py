"""
URL configuration for courses app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Module endpoints
    path('module', views.get_modules, name='get_modules'),
    path('module/<uuid:module_id>', views.get_module_by_id, name='get_module_by_id'),
    
    # Chapter endpoints
    path('chapter/<uuid:chapter_id>', views.get_chapter_by_id, name='get_chapter_by_id'),
    path('chapter/<uuid:chapter_id>/update', views.update_chapter, name='update_chapter'),
    path('chapter/<uuid:chapter_id>/add-stream/<uuid:stream_id>', views.add_stream_to_chapter, name='add_stream_to_chapter'),
    path('module/<uuid:module_id>/chapters', views.get_chapters_by_module, name='get_chapters_by_module'),
    
    # Lesson endpoints
    path('chapter/<uuid:chapter_id>/lessons', views.get_lessons_by_chapter, name='get_lessons_by_chapter'),
    path('lesson/create', views.create_lesson, name='create_lesson'),
    path('lesson/<uuid:lesson_id>', views.get_lesson_by_id, name='get_lesson_by_id'),
    path('lesson/<uuid:lesson_id>/update', views.update_lesson, name='update_lesson'),
    path('lesson/<uuid:lesson_id>/delete', views.delete_lesson, name='delete_lesson'),
    
    # Academic stream endpoints
    path('academic-streams', views.get_academic_streams, name='get_academic_streams'),
    
    # Enrollment endpoints
    path('module/<uuid:module_id>/enroll', views.enroll_in_module, name='enroll_in_module'),
    path('module/<uuid:module_id>/unenroll', views.unenroll_from_module, name='unenroll_from_module'),
    path('enrollments', views.get_enrolled_modules, name='get_enrolled_modules'),
    path('module/<uuid:module_id>/enrollment-status', views.check_enrollment_status, name='check_enrollment_status'),
]
