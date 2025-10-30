from django.urls import path
from . import views

urlpatterns = [
    # Exam management (without 'exams/' prefix since it's already in the base path)
    path('', views.ExamListCreateView.as_view(), name='exam-list'),
    path('<uuid:pk>/', views.ExamRetrieveUpdateDestroyView.as_view(), name='exam-detail'),
    path('chapter/<str:chapter_id>/', views.get_exams_by_chapter, name='exams-by-chapter'),
    path('module/<uuid:module_id>/', views.get_exams_by_module, name='exams-by-module'),
    path('student/', views.get_student_exams, name='student-exams'),
    
    # Exam submissions
    path('submissions/', views.ExamSubmissionListCreateView.as_view(), name='exam-submission-list'),
    path('submissions/<uuid:pk>/', views.ExamSubmissionRetrieveUpdateView.as_view(), name='exam-submission-detail'),
    path('<uuid:exam_id>/submissions/', views.get_exam_submissions, name='exam-submissions'),
    path('<uuid:exam_id>/submit/', views.submit_exam, name='submit-exam'),
]

