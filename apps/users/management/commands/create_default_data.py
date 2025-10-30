"""
Management command to create default admin user and academic streams
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Admin
from apps.courses.models import AcademicStream

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default admin user and academic streams'

    def handle(self, *args, **options):
        # Create default admin user
        admin_email = 'frihaouimohamed@gmail.com'
        admin_password = '07vk640xz'
        
        try:
            admin_user = User.objects.get(email=admin_email)
            self.stdout.write(self.style.WARNING(f'Admin user {admin_email} already exists'))
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                username='admin',
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True
            )
            Admin.objects.create(user=admin_user)
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_email}'))
        
        # Create default academic streams
        streams = [
            ("Mathematics", "الرياضيات"),
            ("Experimental Sciences", "العلوم التجريبية"),
            ("Literature", "الآداب"),
            ("Math-Technique", "رياضيات تقني"),
        ]
        
        for name, name_ar in streams:
            stream, created = AcademicStream.objects.get_or_create(
                name=name,
                defaults={'name_ar': name_ar}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created academic stream: {name} ({name_ar})'))
            else:
                self.stdout.write(self.style.WARNING(f'Academic stream {name} already exists'))
        
        self.stdout.write(self.style.SUCCESS('Default data creation completed'))
