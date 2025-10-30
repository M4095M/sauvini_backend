from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
import uuid
from .models import Exam, ExamSubmission, Quiz, Question, QuizSubmission
from .serializers import (
    ExamSerializer, ExamListSerializer, ExamSubmissionSerializer, 
    CreateExamSubmissionSerializer,
    QuizForStudentSerializer, QuizSerializer, QuizSubmissionSerializer, 
    CreateQuizSubmissionSerializer
)
from apps.courses.models import Chapter, Module, Lesson
from apps.users.models import Student


class ExamListCreateView(generics.ListCreateAPIView):
    """List and create exams"""
    queryset = Exam.objects.select_related('chapter', 'module').prefetch_related('submissions')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ExamListSerializer
        return ExamSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by chapter if provided
        chapter_id = self.request.query_params.get('chapter_id')
        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)
        
        # Filter by module if provided
        module_id = self.request.query_params.get('module_id')
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        """Return exams in frontend-expected shape with pagination metadata.

        Shape: { success: true, data: { exams: ExamWithQuestions[], total, page, per_page } }
        ExamWithQuestions: { exam: <exam_fields>, questions: [] }
        """
        queryset = self.get_queryset().order_by('-created_at')

        # Pagination params (frontend uses page, per_page)
        try:
            page_num = int(request.query_params.get('page', 1))
        except ValueError:
            page_num = 1
        try:
            per_page = int(request.query_params.get('per_page', 50))
        except ValueError:
            per_page = 50

        from django.core.paginator import Paginator
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page_num)

        # Use list serializer for exam portion
        serializer = ExamListSerializer(page_obj.object_list, many=True)
        exams_wrapped = [{ 'exam': exam_data, 'questions': [] } for exam_data in serializer.data]

        return Response({
            'success': True,
            'data': {
                'exams': exams_wrapped,
                'total': paginator.count,
                'page': page_obj.number,
                'per_page': per_page,
            }
        }, status=status.HTTP_200_OK)


class ExamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific exam"""
    queryset = Exam.objects.select_related('chapter', 'module').prefetch_related('submissions')
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_questions(request):
    """Minimal placeholder endpoint to satisfy frontend /questions list.

    Returns paginated empty list using FE's expected shape.
    """
    try:
        page = int(request.query_params.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.query_params.get('per_page', 50))
    except ValueError:
        per_page = 50

    return Response({
        'questions': [],
        'total': 0,
        'page': page,
        'per_page': per_page,
        'total_pages': 0,
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def question_detail(request, question_id):
    """Minimal placeholder for a single question resource."""
    # For now, we do not persist questions; return a not found for GET
    if request.method == 'GET':
        return Response({'message': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        # Echo back the updated payload in expected shape
        payload = request.data or {}
        return Response({
            'question': {
                'id': str(question_id),
                'title': payload.get('title', ''),
                'content': payload.get('content', ''),
                'student_id': payload.get('student_id', ''),
                'student_name': payload.get('student_name', ''),
                'chapter_id': payload.get('chapter_id'),
                'module_id': payload.get('module_id'),
                'subject': payload.get('subject'),
                'status': payload.get('status', 'Pending'),
                'importance': payload.get('importance', 'Normal'),
                'views': 0,
                'likes': 0,
            },
            'tags': payload.get('tag_ids', []),
            'replies': [],
            'attachments': [],
        }, status=status.HTTP_200_OK)

    # DELETE
    return Response({'success': True}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_question(request):
    """Create a question placeholder matching FE expected shape."""
    import uuid
    payload = request.data or {}
    qid = str(uuid.uuid4())
    return Response({
        'question': {
            'id': qid,
            'title': payload.get('title', ''),
            'content': payload.get('content', ''),
            'student_id': getattr(getattr(request.user, 'student', None), 'id', None) or '',
            'student_name': getattr(getattr(request.user, 'student', None), 'first_name', '') + ' ' + getattr(getattr(request.user, 'student', None), 'last_name', ''),
            'chapter_id': payload.get('chapter_id'),
            'module_id': payload.get('module_id'),
            'subject': payload.get('subject'),
            'status': 'Pending',
            'importance': 'Normal',
            'views': 0,
            'likes': 0,
        },
        'tags': payload.get('tag_ids', []),
        'replies': [],
        'attachments': payload.get('attachments', []),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def question_replies(request, question_id):
    """List or create replies for a question (placeholder)."""
    if request.method == 'GET':
        return Response([], status=status.HTTP_200_OK)

    # POST create
    import uuid
    payload = request.data or {}
    rid = str(uuid.uuid4())
    return Response({
        'reply': {
            'id': rid,
            'question_id': str(question_id),
            'author_id': str(getattr(request.user, 'id', '')),
            'author_name': getattr(request.user, 'email', ''),
            'author_type': 'Professor' if hasattr(request.user, 'professor') else 'Student',
            'content': payload.get('content', ''),
            'is_answer': bool(payload.get('is_answer', False)),
            'likes': 0,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def reply_detail(request, reply_id):
    """Update or delete a reply (placeholder)."""
    if request.method == 'PUT':
        payload = request.data or {}
        return Response({
            'id': str(reply_id),
            'question_id': payload.get('question_id', ''),
            'author_id': payload.get('author_id', ''),
            'author_name': payload.get('author_name', ''),
            'author_type': payload.get('author_type', 'Professor'),
            'content': payload.get('content', ''),
            'is_answer': bool(payload.get('is_answer', False)),
            'likes': 0,
        }, status=status.HTTP_200_OK)

    return Response({'success': True}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def question_tags(request):
    """Return a static list of tags (placeholder)."""
    tags = [
        {'id': '1', 'name': 'General', 'color': 'Gray'},
        {'id': '2', 'name': 'Important', 'color': 'Yellow'},
        {'id': '3', 'name': 'MostImportant', 'color': 'Red'},
    ]
    return Response(tags, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exams_by_chapter(request, chapter_id):
    """Get all exams for a specific chapter"""
    try:
        # Handle both UUID and "Chapter:uuid" format
        if chapter_id.startswith('Chapter:'):
            chapter_id = chapter_id.replace('Chapter:', '')
        
        chapter = get_object_or_404(Chapter, id=chapter_id)
        exams = Exam.objects.filter(
            chapter=chapter, 
            is_active=True
        ).select_related('chapter', 'module').prefetch_related('submissions')
        
        serializer = ExamListSerializer(exams, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exams_by_module(request, module_id):
    """Get all exams for a specific module"""
    try:
        module = get_object_or_404(Module, id=module_id)
        exams = Exam.objects.filter(
            module=module, 
            is_active=True
        ).select_related('chapter', 'module').prefetch_related('submissions')
        
        serializer = ExamListSerializer(exams, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


class ExamSubmissionListCreateView(generics.ListCreateAPIView):
    """List and create exam submissions"""
    serializer_class = ExamSubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ExamSubmission.objects.select_related('exam', 'student')
        
        # Filter by exam if provided
        exam_id = self.request.query_params.get('exam_id')
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        
        # Filter by student if provided
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateExamSubmissionSerializer
        return ExamSubmissionSerializer


class ExamSubmissionRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a specific exam submission"""
    queryset = ExamSubmission.objects.select_related('exam', 'student')
    serializer_class = ExamSubmissionSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_exam(request, exam_id):
    """Submit an exam (create or update submission)"""
    try:
        exam = get_object_or_404(Exam, id=exam_id, is_active=True)
        
        # Get or create student profile
        if not hasattr(request.user, 'student'):
            return Response({
                'success': False,
                'error': 'Student profile not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student = request.user.student
        
        # Check if submission already exists
        submission, created = ExamSubmission.objects.get_or_create(
            exam=exam,
            student=student,
            defaults={
                'solution_pdf_url': request.data.get('solution_pdf_url', ''),
                'student_notes': request.data.get('student_notes', ''),
                'status': 'submitted'
            }
        )
        
        if not created:
            # Update existing submission
            submission.solution_pdf_url = request.data.get('solution_pdf_url', submission.solution_pdf_url)
            submission.student_notes = request.data.get('student_notes', submission.student_notes)
            submission.status = 'submitted'
            submission.save()
        
        # Update exam attempts
        exam.attempts += 1
        exam.save()
        
        serializer = ExamSubmissionSerializer(submission)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exam_submissions(request, exam_id):
    """Get all submissions for a specific exam"""
    try:
        exam = get_object_or_404(Exam, id=exam_id, is_active=True)
        submissions = ExamSubmission.objects.filter(
            exam=exam
        ).select_related('student').order_by('-submitted_at')
        
        serializer = ExamSubmissionSerializer(submissions, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_exams(request):
    """Get all exams for the authenticated student"""
    try:
        if not hasattr(request.user, 'student'):
            return Response({
                'success': False,
                'error': 'Student profile not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student = request.user.student
        
        # Get all exams with submission status
        exams = Exam.objects.filter(
            is_active=True
        ).select_related('chapter', 'module').prefetch_related('submissions')
        
        # Add submission status for each exam
        exam_data = []
        for exam in exams:
            submission = exam.submissions.filter(student=student).first()
            exam_serializer = ExamListSerializer(exam)
            exam_dict = exam_serializer.data
            
            if submission:
                exam_dict['submission'] = ExamSubmissionSerializer(submission).data
                exam_dict['status'] = submission.status
            else:
                exam_dict['submission'] = None
                exam_dict['status'] = 'new'
            
            exam_data.append(exam_dict)
        
        return Response({
            'success': True,
            'data': exam_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


# ========================================
# Quiz Endpoints for Students
# ========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quizzes_by_lesson(request, lesson_id):
    """Get all quizzes for a specific lesson"""
    try:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        quizzes = Quiz.objects.filter(
            lesson=lesson,
            is_active=True
        ).prefetch_related('questions').order_by('-created_at')
        
        # Get the first quiz (or return empty structure if no quizzes)
        if quizzes.exists():
            quiz = quizzes.first()
            serializer = QuizForStudentSerializer(quiz)
            
            # Wrap in the expected structure: { quiz: {...}, questions: [...] }
            quiz_data = serializer.data
            questions = quiz_data.pop('questions', [])
            
            # Return first quiz with its questions
            return Response({
                'success': True,
                'data': {
                    'quiz': quiz_data,
                    'questions': questions
                },
                'message': 'Quiz retrieved successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            # No quizzes found for this lesson
            return Response({
                'success': False,
                'data': None,
                'message': 'No quiz found for this lesson',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving quizzes: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_by_id(request, quiz_id):
    """Get a specific quiz by ID"""
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        
        # Check if student has a previous submission
        student = request.user.student if hasattr(request.user, 'student') else None
        previous_submission = None
        if student:
            try:
                previous_submission = QuizSubmission.objects.get(
                    quiz=quiz,
                    student=student
                )
            except QuizSubmission.DoesNotExist:
                pass
        
        serializer = QuizForStudentSerializer(quiz)
        quiz_data = serializer.data
        
        # Extract questions and wrap in expected structure
        questions = quiz_data.pop('questions', [])
        
        # Add submission info if exists
        if previous_submission:
            quiz_data['previous_submission'] = {
                'id': str(previous_submission.id),
                'score': previous_submission.score,
                'passed': previous_submission.passed,
                'submitted_at': previous_submission.submitted_at.isoformat() if previous_submission.submitted_at else None
            }
        
        return Response({
            'success': True,
            'data': {
                'quiz': quiz_data,
                'questions': questions
            },
            'message': 'Quiz retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving quiz: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request, quiz_id):
    """Submit quiz answers and get results"""
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        
        # Check if student is authenticated
        if not hasattr(request.user, 'student'):
            return Response({
                'success': False,
                'message': 'Student profile not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        student = request.user.student
        
        # Check attempts limit
        existing_submissions = QuizSubmission.objects.filter(
            quiz=quiz,
            student=student
        ).count()
        
        if quiz.max_attempts and existing_submissions >= quiz.max_attempts:
            return Response({
                'success': False,
                'message': f'Maximum attempts ({quiz.max_attempts}) reached for this quiz',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create submission
        serializer = CreateQuizSubmissionSerializer(
            data={
                'quiz': quiz_id,
                'answers': request.data.get('answers', {}),
                'time_spent': request.data.get('time_spent', 0)
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            submission = serializer.save()
            response_serializer = QuizSubmissionSerializer(submission)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Quiz submitted successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error submitting quiz: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_submissions(request, quiz_id):
    """Get all quiz submissions for the authenticated student"""
    try:
        if not hasattr(request.user, 'student'):
            return Response({
                'success': False,
                'message': 'Student profile not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        student = request.user.student
        
        submissions = QuizSubmission.objects.filter(
            quiz=quiz,
            student=student
        ).order_by('-submitted_at')
        
        serializer = QuizSubmissionSerializer(submissions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Quiz submissions retrieved successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error retrieving quiz submissions: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# Quiz Endpoints for Professors
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_quiz(request):
    """Create a new quiz for a lesson (Professor only)"""
    try:
        from apps.assessments.serializers import CreateQuizSerializer
        from apps.courses.models import Lesson
        
        lesson_id = request.data.get('lesson_id')
        if not lesson_id:
            return Response({
                'success': False,
                'message': 'Lesson ID is required',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify lesson exists
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Lesson not found',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare quiz data with lesson
        quiz_data = request.data.copy()
        quiz_data['lesson'] = lesson.id
        
        # Create quiz
        serializer = CreateQuizSerializer(data=quiz_data)
        if serializer.is_valid():
            quiz = serializer.save()
            response_serializer = QuizSerializer(quiz)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Quiz created successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error creating quiz: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_quiz(request, quiz_id):
    """Update an existing quiz (Professor only)"""
    try:
        from apps.assessments.serializers import UpdateQuizSerializer
        
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        serializer = UpdateQuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            quiz = serializer.save()
            response_serializer = QuizSerializer(quiz)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Quiz updated successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error updating quiz: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_quiz(request, quiz_id):
    """Delete a quiz (Professor only)"""
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Soft delete by setting is_active=False
        quiz.is_active = False
        quiz.save()
        
        return Response({
            'success': True,
            'message': 'Quiz deleted successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error deleting quiz: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# Question Management Endpoints
# ========================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_question(request):
    """Create a new question for a quiz"""
    try:
        from apps.assessments.serializers import CreateQuestionSerializer, QuestionSerializer
        
        # Create question
        serializer = CreateQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            response_serializer = QuestionSerializer(question)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Question created successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error creating question: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_question(request, question_id):
    """Update an existing question"""
    try:
        from apps.assessments.serializers import UpdateQuestionSerializer, QuestionSerializer
        
        question = get_object_or_404(Question, id=question_id)
        
        serializer = UpdateQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            question = serializer.save()
            response_serializer = QuestionSerializer(question)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': 'Question updated successfully',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': f'Validation error: {serializer.errors}',
                'request_id': str(uuid.uuid4()),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'data': None,
            'message': f'Error updating question: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_question(request, question_id):
    """Delete a question"""
    try:
        question = get_object_or_404(Question, id=question_id)
        question.delete()
        
        return Response({
            'success': True,
            'message': 'Question deleted successfully',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error deleting question: {str(e)}',
            'request_id': str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
