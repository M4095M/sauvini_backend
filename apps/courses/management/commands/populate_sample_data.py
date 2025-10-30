"""
Django management command to populate sample data
"""
from django.core.management.base import BaseCommand
from apps.courses.models import AcademicStream, Module, Chapter, Lesson


class Command(BaseCommand):
    help = 'Populate database with sample academic data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample academic data...')
        
        # Create academic streams
        streams_data = [
            {'name': 'Mathematics', 'name_ar': 'رياضيات'},
            {'name': 'Physics', 'name_ar': 'فيزياء'},
            {'name': 'Chemistry', 'name_ar': 'كيمياء'},
            {'name': 'Biology', 'name_ar': 'علوم الحياة'},
            {'name': 'Computer Science', 'name_ar': 'علوم الحاسوب'},
        ]
        
        streams = []
        for stream_data in streams_data:
            stream, created = AcademicStream.objects.get_or_create(
                name=stream_data['name'],
                defaults={'name_ar': stream_data['name_ar']}
            )
            streams.append(stream)
            if created:
                self.stdout.write(f'Created academic stream: {stream.name}')
        
        # Create modules
        modules_data = [
            {
                'name': 'الجبر الأساسي',
                'description': 'مقدمة في الجبر والعمليات الجبرية الأساسية',
                'color': '#FF6B6B',
                'academic_streams': ['Mathematics']
            },
            {
                'name': 'الهندسة التحليلية',
                'description': 'دراسة الهندسة باستخدام الإحداثيات والجبر',
                'color': '#4ECDC4',
                'academic_streams': ['Mathematics']
            },
            {
                'name': 'الميكانيكا الكلاسيكية',
                'description': 'دراسة حركة الأجسام والقوى المؤثرة عليها',
                'color': '#45B7D1',
                'academic_streams': ['Physics']
            },
            {
                'name': 'الكيمياء العضوية',
                'description': 'دراسة المركبات العضوية وخصائصها',
                'color': '#96CEB4',
                'academic_streams': ['Chemistry']
            },
            {
                'name': 'البرمجة الأساسية',
                'description': 'مقدمة في البرمجة ومفاهيمها الأساسية',
                'color': '#FFEAA7',
                'academic_streams': ['Computer Science']
            }
        ]
        
        modules = []
        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=module_data['name'],
                defaults={
                    'description': module_data['description'],
                    'color': module_data['color']
                }
            )
            
            # Add academic streams
            for stream_name in module_data['academic_streams']:
                stream = AcademicStream.objects.get(name=stream_name)
                module.academic_streams.add(stream)
            
            modules.append(module)
            if created:
                self.stdout.write(f'Created module: {module.name}')
        
        # Create chapters for the first module (الجبر الأساسي)
        algebra_module = modules[0]
        chapters_data = [
            {
                'name': 'مقدمة في الجبر',
                'description': 'تعريف الجبر والمفاهيم الأساسية',
                'price': 1000.00
            },
            {
                'name': 'المتغيرات والمعادلات',
                'description': 'كيفية التعامل مع المتغيرات وحل المعادلات',
                'price': 1500.00
            },
            {
                'name': 'العمليات الجبرية',
                'description': 'الجمع والطرح والضرب والقسمة في الجبر',
                'price': 2000.00
            }
        ]
        
        chapters = []
        for chapter_data in chapters_data:
            chapter, created = Chapter.objects.get_or_create(
                name=chapter_data['name'],
                module=algebra_module,
                defaults={
                    'description': chapter_data['description'],
                    'price': chapter_data['price']
                }
            )
            chapters.append(chapter)
            if created:
                self.stdout.write(f'Created chapter: {chapter.name}')
        
        # Create lessons for the first chapter
        intro_chapter = chapters[0]
        lessons_data = [
            {
                'title': 'ما هو الجبر؟',
                'description': 'تعريف الجبر وأهميته في الرياضيات',
                'duration': 30,
                'order': 1
            },
            {
                'title': 'تاريخ الجبر',
                'description': 'نظرة تاريخية على تطور الجبر',
                'duration': 25,
                'order': 2
            }
        ]
        
        for lesson_data in lessons_data:
            lesson, created = Lesson.objects.get_or_create(
                title=lesson_data['title'],
                chapter=intro_chapter,
                defaults={
                    'description': lesson_data['description'],
                    'duration': lesson_data['duration'],
                    'order': lesson_data['order']
                }
            )
            if created:
                self.stdout.write(f'Created lesson: {lesson.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated sample data!')
        )
