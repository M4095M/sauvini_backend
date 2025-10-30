from rest_framework import serializers
from .models import Exam, ExamSubmission, Quiz, Question, QuizSubmission
from apps.courses.serializers import ChapterSerializer, ModuleSerializer
from apps.users.models import Student


class StudentSerializer(serializers.ModelSerializer):
    """Simple student serializer for exam submissions"""
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email', 'level']


class ExamSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for exam submissions matching frontend structure"""
    student = StudentSerializer(read_only=True)
    student_id = serializers.UUIDField(write_only=True)
    examId = serializers.CharField(source='exam.id', read_only=True)
    studentId = serializers.CharField(source='student.id', read_only=True)
    submittedAt = serializers.DateTimeField(source='submitted_at', read_only=True)
    solutionPdfUrl = serializers.URLField(source='solution_pdf_url', read_only=True)
    studentNotes = serializers.CharField(source='student_notes', read_only=True)
    professorNotes = serializers.CharField(source='professor_notes', read_only=True)
    professorReviewPdfUrl = serializers.URLField(source='professor_review_pdf_url', read_only=True)
    
    class Meta:
        model = ExamSubmission
        fields = [
            'id', 'examId', 'studentId', 'submittedAt', 'grade', 
            'status', 'solutionPdfUrl', 'studentNotes', 'professorNotes', 
            'professorReviewPdfUrl', 'exam', 'student', 'student_id', 
            'submitted_at', 'solution_pdf_url', 'student_notes', 
            'professor_notes', 'professor_review_pdf_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at', 'updated_at']


class ExamSerializer(serializers.ModelSerializer):
    """Serializer for exams matching frontend structure"""
    chapter = ChapterSerializer(read_only=True)
    chapter_id = serializers.UUIDField(write_only=True)
    module = ModuleSerializer(read_only=True)
    module_id = serializers.UUIDField(write_only=True)
    submissions = ExamSubmissionSerializer(many=True, read_only=True)
    
    # Frontend UI fields (computed from relationships)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    chapter_image = serializers.CharField(source='chapter.image_url', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)
    module_color = serializers.CharField(source='module.color', read_only=True)
    
    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'chapter', 'chapter_id', 'module', 'module_id',
            'status', 'total_questions', 'duration', 'passing_score', 'attempts', 
            'max_attempts', 'is_unlocked', 'is_active', 'created_at', 'updated_at',
            'submissions', 'chapter_name', 'chapter_image', 'module_name', 'module_color'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'attempts']
    
    def create(self, validated_data):
        # Extract the foreign key IDs
        chapter_id = validated_data.pop('chapter_id')
        module_id = validated_data.pop('module_id')
        
        # Create the exam with the foreign key objects
        exam = Exam.objects.create(
            chapter_id=chapter_id,
            module_id=module_id,
            **validated_data
        )
        return exam
    
    def update(self, instance, validated_data):
        # Handle foreign key updates if provided
        if 'chapter_id' in validated_data:
            instance.chapter_id = validated_data.pop('chapter_id')
        if 'module_id' in validated_data:
            instance.module_id = validated_data.pop('module_id')
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ExamListSerializer(serializers.ModelSerializer):
    """Simplified serializer for exam lists"""
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    chapter_image = serializers.CharField(source='chapter.image_url', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)
    module_color = serializers.CharField(source='module.color', read_only=True)
    submissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'status', 'total_questions', 'duration', 
            'passing_score', 'attempts', 'max_attempts', 'is_unlocked', 'is_active',
            'created_at', 'chapter_name', 'chapter_image', 'module_name', 'module_color',
            'submissions_count'
        ]
    
    def get_submissions_count(self, obj):
        return obj.submissions.count()


class CreateExamSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating exam submissions"""
    
    class Meta:
        model = ExamSubmission
        fields = [
            'exam', 'student', 'solution_pdf_url', 'student_notes'
        ]
    
    def create(self, validated_data):
        # Set the student from the request user if not provided
        if 'student' not in validated_data:
            request = self.context.get('request')
            if request and hasattr(request.user, 'student'):
                validated_data['student'] = request.user.student
            else:
                raise serializers.ValidationError("Student information is required")
        
        return super().create(validated_data)


# Quiz Serializers
class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions"""
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'options', 
            'correct_answer', 'points', 'explanation', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuestionForStudentSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions shown to students (without correct answers)"""
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_type', 'options', 
            'points', 'explanation', 'order'
        ]
        read_only_fields = ['id']


class CreateQuestionSerializer(serializers.ModelSerializer):
    """Serializer for creating quiz questions"""
    
    class Meta:
        model = Question
        fields = [
            'quiz', 'question_text', 'question_type', 'options',
            'correct_answer', 'points', 'explanation', 'order'
        ]
    
    def validate_points(self, value):
        """Validate points are positive"""
        if value <= 0:
            raise serializers.ValidationError("Points must be positive")
        return value


class UpdateQuestionSerializer(serializers.ModelSerializer):
    """Serializer for updating quiz questions"""
    
    class Meta:
        model = Question
        fields = [
            'question_text', 'question_type', 'options',
            'correct_answer', 'points', 'explanation', 'order'
        ]
    
    def validate_points(self, value):
        """Validate points are positive"""
        if value <= 0:
            raise serializers.ValidationError("Points must be positive")
        return value


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for quizzes"""
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'lesson', 'time_limit', 
            'passing_score', 'max_attempts', 'is_active',
            'questions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuizForStudentSerializer(serializers.ModelSerializer):
    """Serializer for quizzes shown to students"""
    questions = QuestionForStudentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'time_limit', 
            'passing_score', 'max_attempts',
            'questions', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class QuizSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for quiz submissions"""
    student = StudentSerializer(read_only=True)
    
    class Meta:
        model = QuizSubmission
        fields = [
            'id', 'quiz', 'student', 'answers', 'score', 'passed',
            'time_spent', 'submitted_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateQuizSerializer(serializers.ModelSerializer):
    """Serializer for creating quizzes"""
    
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'lesson', 'time_limit',
            'passing_score', 'max_attempts', 'is_active'
        ]
    
    def validate(self, data):
        passing_score = data.get('passing_score', 0)
        if passing_score < 0 or passing_score > 100:
            raise serializers.ValidationError(
                "Passing score must be between 0 and 100"
            )
        return data


class UpdateQuizSerializer(serializers.ModelSerializer):
    """Serializer for updating quizzes"""
    
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'time_limit',
            'passing_score', 'max_attempts', 'is_active'
        ]
    
    def validate(self, data):
        passing_score = data.get('passing_score', 0)
        if passing_score < 0 or passing_score > 100:
            raise serializers.ValidationError(
                "Passing score must be between 0 and 100"
            )
        return data


class CreateQuizSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating quiz submissions"""
    
    class Meta:
        model = QuizSubmission
        fields = ['quiz', 'answers', 'time_spent']
    
    def create(self, validated_data):
        # Set the student from the request user
        request = self.context.get('request')
        if request and hasattr(request.user, 'student'):
            validated_data['student'] = request.user.student
        else:
            raise serializers.ValidationError("Student information is required")
        
        # Set submitted_at
        from django.utils import timezone
        validated_data['submitted_at'] = timezone.now()
        
        # Calculate score and passed status
        quiz = validated_data['quiz']
        answers = validated_data['answers']
        
        # Grade the submission
        total_points = 0
        earned_points = 0
        
        for question in quiz.questions.all():
            total_points += question.points
            if str(question.id) in answers:
                if str(answers[str(question.id)]).lower() == str(question.correct_answer).lower():
                    earned_points += question.points
        
        score = round((earned_points / total_points) * 100, 2) if total_points > 0 else 0
        passed = score >= quiz.passing_score
        
        validated_data['score'] = score
        validated_data['passed'] = passed
        
        return super().create(validated_data)
