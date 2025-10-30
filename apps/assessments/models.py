"""
Assessment models for Quiz, Exercise, Exam, and Question
"""
from django.db import models
from django.utils import timezone
import uuid


class QuestionType(models.TextChoices):
    """Question type choices matching Rust enum"""
    MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
    TRUE_FALSE = 'true_false', 'True/False'
    SHORT_ANSWER = 'short_answer', 'Short Answer'


class Quiz(models.Model):
    """Quiz model matching Rust Quiz struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='quizzes')
    time_limit = models.IntegerField(null=True, blank=True)  # in minutes
    passing_score = models.IntegerField()  # 0-100
    max_attempts = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes'
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class Question(models.Model):
    """Question model matching Rust QuizQuestion struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    options = models.JSONField(null=True, blank=True)  # For multiple choice questions
    correct_answer = models.TextField()
    points = models.IntegerField()
    explanation = models.TextField(blank=True, null=True)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'questions'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"


class QuizSubmission(models.Model):
    """Quiz submission model matching Rust QuizSubmission struct"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='quiz_submissions')
    answers = models.JSONField()  # question_id -> answer
    score = models.IntegerField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    time_spent = models.IntegerField(null=True, blank=True)  # in minutes
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quiz_submissions'
        unique_together = ['quiz', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.quiz.title}"


class Exercise(models.Model):
    """Exercise model (placeholder for future implementation)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='exercises')
    content = models.TextField()
    solution = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exercises'
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class Exam(models.Model):
    """Exam model matching frontend structure"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('submitted', 'Submitted'),
        ('failed', 'Failed'),
        ('passed', 'Passed'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    chapter = models.ForeignKey('courses.Chapter', on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    module = models.ForeignKey('courses.Module', on_delete=models.CASCADE, related_name='exams')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    total_questions = models.IntegerField(default=0)
    duration = models.IntegerField()  # in minutes
    passing_score = models.IntegerField()  # percentage (0-100)
    attempts = models.IntegerField(default=0)  # number of attempts made
    max_attempts = models.IntegerField(default=3)
    is_unlocked = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exams'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.module.name} - {self.chapter.name} - {self.title}"


class ExamSubmission(models.Model):
    """Exam submission model matching frontend structure"""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='exam_submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)  # Professor's assigned grade (0-20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    solution_pdf_url = models.URLField(max_length=500, blank=True, null=True)  # Student's uploaded solution
    student_notes = models.TextField(blank=True, null=True)  # Student's additional notes
    professor_notes = models.TextField(blank=True, null=True)  # Professor's review notes
    professor_review_pdf_url = models.URLField(max_length=500, blank=True, null=True)  # Optional professor review file
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exam_submissions'
        ordering = ['-submitted_at']
        unique_together = ['exam', 'student']  # One submission per student per exam
    
    def __str__(self):
        return f"{self.student} - {self.exam.title} ({self.status})"