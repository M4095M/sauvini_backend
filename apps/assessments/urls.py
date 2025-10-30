from django.urls import path
from . import views

urlpatterns = [
    # Exam management
    path('exams/', views.ExamListCreateView.as_view(), name='exam-list-create'),
    path('exams/<uuid:pk>/', views.ExamRetrieveUpdateDestroyView.as_view(), name='exam-detail'),
    path('exams/chapter/<str:chapter_id>/', views.get_exams_by_chapter, name='exams-by-chapter'),
    path('exams/module/<uuid:module_id>/', views.get_exams_by_module, name='exams-by-module'),
    path('exams/student/', views.get_student_exams, name='student-exams'),
    
    # Exam submissions
    path('exam-submissions/', views.ExamSubmissionListCreateView.as_view(), name='exam-submission-list-create'),
    path('exam-submissions/<uuid:pk>/', views.ExamSubmissionRetrieveUpdateView.as_view(), name='exam-submission-detail'),
    path('exams/<uuid:exam_id>/submissions/', views.get_exam_submissions, name='exam-submissions'),
    path('exams/<uuid:exam_id>/submit/', views.submit_exam, name='submit-exam'),
    # Questions (placeholder to match FE)
    path('questions', views.list_questions, name='questions-list'),
    path('questions/<uuid:question_id>', views.question_detail, name='question-detail'),
    path('questions/<uuid:question_id>/replies', views.question_replies, name='question-replies'),
    path('questions/replies/<uuid:reply_id>', views.reply_detail, name='reply-detail'),
    path('questions/tags', views.question_tags, name='question-tags'),
    # Quiz endpoints - Student access
    path('quizzes/lesson/<uuid:lesson_id>', views.get_quizzes_by_lesson, name='quizzes-by-lesson'),
    path('quizzes/<uuid:quiz_id>/detail', views.get_quiz_by_id, name='quiz-detail'),
    path('quizzes/<uuid:quiz_id>/submit', views.submit_quiz, name='submit-quiz'),
    path('quizzes/<uuid:quiz_id>/submissions', views.get_quiz_submissions, name='quiz-submissions'),
    # Professor quiz management endpoints - CRUD operations
    path('quizzes/create', views.create_quiz, name='create-quiz'),
    path('quizzes/<uuid:quiz_id>/update', views.update_quiz, name='update-quiz'),
    path('quizzes/<uuid:quiz_id>/delete', views.delete_quiz, name='delete-quiz'),
    # Question management endpoints
    path('questions/create', views.create_question, name='create-question'),
    path('questions/<uuid:question_id>/update', views.update_question, name='update-question'),
    path('questions/<uuid:question_id>/delete', views.delete_question, name='delete-question'),
]
