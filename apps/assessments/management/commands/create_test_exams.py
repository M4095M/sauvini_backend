from django.core.management.base import BaseCommand
from apps.assessments.models import Exam
from apps.courses.models import Module, Chapter
from apps.users.models import Student
import uuid


class Command(BaseCommand):
    help = 'Create test exams data'

    def handle(self, *args, **options):
        # Create test modules and chapters if they don't exist
        math_module, created = Module.objects.get_or_create(
            name="Mathematics",
            defaults={
                'description': 'Mathematics course',
                'color': '#FFD700'  # Gold/yellow
            }
        )
        
        physics_module, created = Module.objects.get_or_create(
            name="Physics",
            defaults={
                'description': 'Physics course',
                'color': '#0000FF'  # Blue
            }
        )
        
        biology_module, created = Module.objects.get_or_create(
            name="Biology",
            defaults={
                'description': 'Biology course',
                'color': '#00FF00'  # Green
            }
        )
        
        # Create test chapters
        calc_chapter, created = Chapter.objects.get_or_create(
            name="Calculus Fundamentals",
            module=math_module,
            defaults={
                'description': 'Introduction to calculus',
                'price': 1500.00
            }
        )
        
        functions_chapter, created = Chapter.objects.get_or_create(
            name="Advanced Functions",
            module=math_module,
            defaults={
                'description': 'Advanced mathematical functions',
                'price': 1800.00
            }
        )
        
        geometry_chapter, created = Chapter.objects.get_or_create(
            name="Geometry & Vectors",
            module=math_module,
            defaults={
                'description': 'Coordinate geometry and vectors',
                'price': 1200.00
            }
        )
        
        mechanics_chapter, created = Chapter.objects.get_or_create(
            name="Physics Mechanics",
            module=physics_module,
            defaults={
                'description': 'Mechanics and motion',
                'price': 2000.00
            }
        )
        
        cell_bio_chapter, created = Chapter.objects.get_or_create(
            name="Cell Biology",
            module=biology_module,
            defaults={
                'description': 'Introduction to cell biology',
                'price': 1600.00
            }
        )
        
        # Create test exams
        exams_data = [
            {
                'title': 'Calculus Fundamentals Final Exam',
                'description': 'Test your understanding of derivatives and basic integration',
                'chapter': calc_chapter,
                'module': math_module,
                'status': 'new',
                'total_questions': 20,
                'duration': 60,
                'passing_score': 70,
                'attempts': 0,
                'max_attempts': 3,
                'is_unlocked': True,
            },
            {
                'title': 'Advanced Functions Assessment',
                'description': 'Comprehensive test on logarithmic, exponential and trigonometric functions',
                'chapter': functions_chapter,
                'module': math_module,
                'status': 'new',
                'total_questions': 25,
                'duration': 75,
                'passing_score': 75,
                'attempts': 0,
                'max_attempts': 3,
                'is_unlocked': True,
            },
            {
                'title': 'Geometry & Vectors Exam',
                'description': 'Test your knowledge of coordinate geometry and vector operations',
                'chapter': geometry_chapter,
                'module': math_module,
                'status': 'new',
                'total_questions': 18,
                'duration': 50,
                'passing_score': 70,
                'attempts': 0,
                'max_attempts': 3,
                'is_unlocked': True,
            },
            {
                'title': 'Physics Mechanics Exam',
                'description': 'Test your understanding of mechanics and motion',
                'chapter': mechanics_chapter,
                'module': physics_module,
                'status': 'new',
                'total_questions': 22,
                'duration': 80,
                'passing_score': 70,
                'attempts': 0,
                'max_attempts': 3,
                'is_unlocked': True,
            },
            {
                'title': 'Cell Biology Exam',
                'description': 'Test your knowledge of cell structure and function',
                'chapter': cell_bio_chapter,
                'module': biology_module,
                'status': 'new',
                'total_questions': 15,
                'duration': 45,
                'passing_score': 70,
                'attempts': 0,
                'max_attempts': 3,
                'is_unlocked': True,
            },
        ]
        
        created_count = 0
        for exam_data in exams_data:
            exam, created = Exam.objects.get_or_create(
                title=exam_data['title'],
                chapter=exam_data['chapter'],
                defaults=exam_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created exam: {exam.title}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} test exams')
        )
