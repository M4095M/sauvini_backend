"""
Django management command to clean up academic streams to only keep the 6 specified ones
and convert their names to English
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.courses.models import AcademicStream, Module, Chapter, Lesson


class Command(BaseCommand):
    help = 'Clean up academic streams to keep only 6 specified ones and convert names to English'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # The 6 streams to keep with their English names
        streams_to_keep = {
            "1c6492de-a922-4afa-9e68-030395e01e40": {
                "name": "Experimental Sciences",
                "name_ar": "علوم تجريبية"
            },
            "1d161706-7833-4e14-9ce8-1653a70ac862": {
                "name": "Technical Mathematics",
                "name_ar": "تقني رياضي"
            },
            "1f3bab99-641b-40dc-854f-0bf4c0d3d9fa": {
                "name": "Mathematics",
                "name_ar": "رياضيات"
            },
            "4a25face-9d68-48ef-a331-8c017c10b2bf": {
                "name": "Natural Sciences",
                "name_ar": "علوم طبيعية"
            },
            "5372521f-4cc5-4c46-9ecd-d21a73e12ab6": {
                "name": "Literature and Philosophy",
                "name_ar": "اداب و فلسفة"
            },
            "9b9af5e7-186b-4216-9e23-7918de756386": {
                "name": "Management and Economics",
                "name_ar": "تسيير و اقتصاد"
            }
        }
        
        self.stdout.write('Analyzing current academic streams...')
        
        # Get all current streams
        all_streams = AcademicStream.objects.all()
        streams_to_delete = []
        streams_to_update = []
        
        with transaction.atomic():
            for stream in all_streams:
                stream_id = str(stream.id)
                
                if stream_id in streams_to_keep:
                    # This stream should be kept and updated
                    new_name = streams_to_keep[stream_id]["name"]
                    new_name_ar = streams_to_keep[stream_id]["name_ar"]
                    
                    if stream.name != new_name or stream.name_ar != new_name_ar:
                        streams_to_update.append({
                            'stream': stream,
                            'old_name': stream.name,
                            'new_name': new_name,
                            'new_name_ar': new_name_ar
                        })
                else:
                    # This stream should be deleted
                    streams_to_delete.append(stream)
            
            # Show what will be updated
            if streams_to_update:
                self.stdout.write(f'\n📝 Streams to be updated ({len(streams_to_update)}):')
                for update in streams_to_update:
                    self.stdout.write(f'  - {update["old_name"]} → {update["new_name"]}')
            
            # Show what will be deleted
            if streams_to_delete:
                self.stdout.write(f'\n🗑️  Streams to be deleted ({len(streams_to_delete)}):')
                for stream in streams_to_delete:
                    # Check relationships before deletion
                    module_count = Module.objects.filter(academic_streams=stream).count()
                    chapter_count = Chapter.objects.filter(academic_streams=stream).count()
                    lesson_count = Lesson.objects.filter(academic_streams=stream).count()
                    total_relations = module_count + chapter_count + lesson_count
                    
                    if total_relations > 0:
                        self.stdout.write(f'  ⚠️  {stream.name} - HAS {total_relations} RELATIONSHIPS!')
                        self.stdout.write(f'      Modules: {module_count}, Chapters: {chapter_count}, Lessons: {lesson_count}')
                    else:
                        self.stdout.write(f'  ✅ {stream.name} - No relationships')
            
            if not dry_run:
                # Update stream names
                for update in streams_to_update:
                    stream = update['stream']
                    stream.name = update['new_name']
                    stream.name_ar = update['new_name_ar']
                    stream.save()
                    self.stdout.write(f'Updated: {update["old_name"]} → {update["new_name"]}')
                
                # Delete streams without relationships
                deleted_count = 0
                for stream in streams_to_delete:
                    # Check if stream has relationships
                    module_count = Module.objects.filter(academic_streams=stream).count()
                    chapter_count = Chapter.objects.filter(academic_streams=stream).count()
                    lesson_count = Lesson.objects.filter(academic_streams=stream).count()
                    
                    if module_count == 0 and chapter_count == 0 and lesson_count == 0:
                        stream.delete()
                        deleted_count += 1
                        self.stdout.write(f'Deleted: {stream.name}')
                    else:
                        self.stdout.write(f'⚠️  SKIPPED {stream.name} - Has relationships!')
                
                # Final summary
                remaining_streams = AcademicStream.objects.all()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ Cleanup completed!\n'
                        f'- Streams updated: {len(streams_to_update)}\n'
                        f'- Streams deleted: {deleted_count}\n'
                        f'- Streams with relationships skipped: {len(streams_to_delete) - deleted_count}\n'
                        f'- Total streams remaining: {remaining_streams.count()}\n'
                        f'- Final streams:'
                    )
                )
                
                for stream in remaining_streams.order_by('name'):
                    self.stdout.write(f'  📚 {stream.name} ({stream.name_ar})')
                    
            else:
                # Dry run summary
                streams_with_relations = [s for s in streams_to_delete if 
                    Module.objects.filter(academic_streams=s).count() > 0 or
                    Chapter.objects.filter(academic_streams=s).count() > 0 or
                    Lesson.objects.filter(academic_streams=s).count() > 0]
                
                self.stdout.write(
                    self.style.WARNING(
                        f'\n📊 Dry run summary:\n'
                        f'- Streams to update: {len(streams_to_update)}\n'
                        f'- Streams to delete: {len(streams_to_delete)}\n'
                        f'- Streams with relationships (would be skipped): {len(streams_with_relations)}\n'
                        f'- Current total: {all_streams.count()}\n'
                        f'- Would remain: {len(streams_to_keep)}'
                    )
                )
