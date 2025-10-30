"""
Django management command to update academic streams
Adds missing streams and removes duplicates
"""
from django.core.management.base import BaseCommand
from apps.courses.models import AcademicStream


class Command(BaseCommand):
    help = 'Update academic streams - add missing ones and remove duplicates'

    def handle(self, *args, **options):
        self.stdout.write('Updating academic streams...')
        
        # Define the complete list of academic streams that should exist
        streams_data = [
            {'name': 'علوم تجريبية', 'name_ar': 'علوم تجريبية'},
            {'name': 'رياضيات', 'name_ar': 'رياضيات'},
            {'name': 'تقني رياضي', 'name_ar': 'تقني رياضي'},
            {'name': 'تسيير و اقتصاد', 'name_ar': 'تسيير و اقتصاد'},
            {'name': 'اداب و فلسفة', 'name_ar': 'اداب و فلسفة'},
            # Additional streams that might be needed
            {'name': 'علوم طبيعية', 'name_ar': 'علوم طبيعية'},
            {'name': 'علوم إنسانية', 'name_ar': 'علوم إنسانية'},
            {'name': 'تقني رياضي - تخصص', 'name_ar': 'تقني رياضي - تخصص'},
            {'name': 'تسيير و اقتصاد - تخصص', 'name_ar': 'تسيير و اقتصاد - تخصص'},
        ]
        
        # Track created and updated streams
        created_count = 0
        updated_count = 0
        duplicate_count = 0
        
        # First, find and remove duplicates
        self.stdout.write('Checking for duplicates...')
        all_streams = AcademicStream.objects.all()
        seen_names = set()
        duplicates_to_delete = []
        
        for stream in all_streams:
            if stream.name in seen_names:
                duplicates_to_delete.append(stream)
                duplicate_count += 1
                self.stdout.write(f'Found duplicate: {stream.name} (ID: {stream.id})')
            else:
                seen_names.add(stream.name)
        
        # Delete duplicates
        for duplicate in duplicates_to_delete:
            duplicate.delete()
            self.stdout.write(f'Deleted duplicate: {duplicate.name}')
        
        # Add or update streams
        for stream_data in streams_data:
            stream, created = AcademicStream.objects.get_or_create(
                name=stream_data['name'],
                defaults={'name_ar': stream_data['name_ar']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created academic stream: {stream.name}')
            else:
                # Update name_ar if it's different
                if stream.name_ar != stream_data['name_ar']:
                    stream.name_ar = stream_data['name_ar']
                    stream.save()
                    updated_count += 1
                    self.stdout.write(f'Updated academic stream: {stream.name}')
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Academic streams update completed!\n'
                f'- Created: {created_count}\n'
                f'- Updated: {updated_count}\n'
                f'- Duplicates removed: {duplicate_count}\n'
                f'- Total streams now: {AcademicStream.objects.count()}'
            )
        )
