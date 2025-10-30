"""
URL configuration for progress tracking
"""
from django.urls import path
from . import views

urlpatterns = [
    # Lesson progress endpoints
    path('lesson/<uuid:lesson_id>/progress', views.get_lesson_progress, name='get_lesson_progress'),
    path('lesson/<uuid:lesson_id>/progress/update', views.update_lesson_progress, name='update_lesson_progress'),
    path('chapter/<uuid:chapter_id>/lessons/progress', views.get_chapter_lesson_progress, name='get_chapter_lesson_progress'),
    
    # Chapter progress endpoints
    path('chapter/<uuid:chapter_id>/progress', views.get_chapter_progress, name='get_chapter_progress'),
    path('chapter/<uuid:chapter_id>/progress/update', views.update_chapter_progress, name='update_chapter_progress'),
    
    # Module progress endpoints
    path('module/<uuid:module_id>/progress', views.get_module_progress, name='get_module_progress'),
    
    # Student progress summary
    path('summary', views.get_student_progress_summary, name='get_student_progress_summary'),
]

