"""
Management command to create default admin user and academic streams
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.utils import DatabaseError
from apps.users.models import Admin
from apps.courses.models import AcademicStream

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default admin user and academic streams'

    def fix_table_charset(self):
        """Fix the charset of the academic_streams table columns if needed"""
        try:
            with connection.cursor() as cursor:
                # Check if columns need charset fixing
                cursor.execute("""
                    SELECT COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'academic_streams'
                    AND COLUMN_NAME IN ('name', 'name_ar')
                """)
                results = cursor.fetchall()
                
                needs_fix = False
                for col_name, charset, collation in results:
                    if charset and charset.lower() != 'utf8mb4':
                        needs_fix = True
                        break
                    if collation and 'utf8mb4' not in collation.lower():
                        needs_fix = True
                        break
                
                if needs_fix or not results:
                    self.stdout.write(self.style.WARNING(
                        'Fixing academic_streams table column charset to utf8mb4...'
                    ))
                    
                    # Convert individual columns to avoid foreign key constraint issues
                    # We can safely convert VARCHAR columns even with foreign keys
                    cursor.execute("""
                        ALTER TABLE academic_streams 
                        MODIFY COLUMN name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """)
                    
                    cursor.execute("""
                        ALTER TABLE academic_streams 
                        MODIFY COLUMN name_ar VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(
                        'Successfully fixed academic_streams column charset to utf8mb4'
                    ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'Could not fix column charset automatically: {e}. '
                'You may need to run this SQL manually: '
                'ALTER TABLE academic_streams MODIFY COLUMN name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; '
                'ALTER TABLE academic_streams MODIFY COLUMN name_ar VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
            ))

    def handle(self, *args, **options):
        # Create default admin user
        admin_email = 'admin@sauvini.com'
        admin_password = 'Admin123!'
        
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
        
        # Try to fix table charset if needed (for MySQL/MariaDB)
        if connection.vendor == 'mysql':
            self.fix_table_charset()
        
        # Create default academic streams
        streams = [
            ("Mathematics", "الرياضيات"),
            ("Experimental Sciences", "العلوم التجريبية"),
            ("Literature", "الآداب"),
            ("Math-Technique", "رياضيات تقني"),
        ]
        
        for name, name_ar in streams:
            try:
                stream, created = AcademicStream.objects.get_or_create(
                    name=name,
                    defaults={'name_ar': name_ar}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created academic stream: {name} ({name_ar})'))
                else:
                    # Update name_ar if it exists but is different
                    if stream.name_ar != name_ar:
                        try:
                            stream.name_ar = name_ar
                            stream.save()
                            self.stdout.write(self.style.SUCCESS(f'Updated academic stream: {name} ({name_ar})'))
                        except DatabaseError as e:
                            self.stdout.write(self.style.ERROR(
                                f'Could not update academic stream {name}: {e}. '
                                'Table charset may need to be fixed manually.'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(f'Academic stream {name} already exists'))
            except DatabaseError as e:
                self.stdout.write(self.style.ERROR(
                    f'Error creating academic stream {name}: {e}. '
                    'Please ensure the database table uses utf8mb4 charset. '
                    'Run: ALTER TABLE academic_streams CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
                ))
        
        self.stdout.write(self.style.SUCCESS('Default data creation completed'))
