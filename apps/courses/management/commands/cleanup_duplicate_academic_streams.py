"""
Django management command to safely clean up duplicate academic streams
Preserves streams with relationships and merges them into the most connected stream
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.courses.models import AcademicStream, Module, Chapter, Lesson
from collections import defaultdict


class Command(BaseCommand):
    help = 'Safely clean up duplicate academic streams while preserving relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Analyzing academic streams for duplicates...')
        
        # Group streams by name to find duplicates
        streams_by_name = defaultdict(list)
        all_streams = AcademicStream.objects.all()
        
        for stream in all_streams:
            streams_by_name[stream.name].append(stream)
        
        duplicates_found = 0
        streams_to_delete = []
        relationships_transferred = 0
        
        with transaction.atomic():
            for name, streams in streams_by_name.items():
                if len(streams) > 1:
                    duplicates_found += len(streams) - 1
                    self.stdout.write(f'\nFound {len(streams)} duplicates for "{name}":')
                    
                    # Calculate relationship counts for each stream
                    stream_relationships = []
                    for stream in streams:
                        module_count = Module.objects.filter(academic_streams=stream).count()
                        chapter_count = Chapter.objects.filter(academic_streams=stream).count()
                        lesson_count = Lesson.objects.filter(academic_streams=stream).count()
                        total_relationships = module_count + chapter_count + lesson_count
                        
                        stream_relationships.append({
                            'stream': stream,
                            'module_count': module_count,
                            'chapter_count': chapter_count,
                            'lesson_count': lesson_count,
                            'total': total_relationships
                        })
                        
                        self.stdout.write(
                            f'  - {stream.id}: {total_relationships} relationships '
                            f'(Modules: {module_count}, Chapters: {chapter_count}, Lessons: {lesson_count})'
                        )
                    
                    # Sort by total relationships (descending) to keep the most connected one
                    stream_relationships.sort(key=lambda x: x['total'], reverse=True)
                    keeper = stream_relationships[0]['stream']
                    duplicates = [rel['stream'] for rel in stream_relationships[1:]]
                    
                    self.stdout.write(f'  → Keeping: {keeper.id} (most relationships)')
                    self.stdout.write(f'  → Will delete: {[d.id for d in duplicates]}')
                    
                    if not dry_run:
                        # Transfer relationships from duplicates to keeper
                        for duplicate in duplicates:
                            # Transfer module relationships
                            modules = Module.objects.filter(academic_streams=duplicate)
                            for module in modules:
                                module.academic_streams.remove(duplicate)
                                module.academic_streams.add(keeper)
                                relationships_transferred += 1
                            
                            # Transfer chapter relationships
                            chapters = Chapter.objects.filter(academic_streams=duplicate)
                            for chapter in chapters:
                                chapter.academic_streams.remove(duplicate)
                                chapter.academic_streams.add(keeper)
                                relationships_transferred += 1
                            
                            # Transfer lesson relationships
                            lessons = Lesson.objects.filter(academic_streams=duplicate)
                            for lesson in lessons:
                                lesson.academic_streams.remove(duplicate)
                                lesson.academic_streams.add(keeper)
                                relationships_transferred += 1
                            
                            # Mark for deletion
                            streams_to_delete.append(duplicate)
                    
                    streams_to_delete.extend(duplicates)
        
        # Delete duplicates
        if streams_to_delete and not dry_run:
            deleted_count = 0
            for stream in streams_to_delete:
                stream.delete()
                deleted_count += 1
                self.stdout.write(f'Deleted duplicate: {stream.name} ({stream.id})')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCleanup completed!\n'
                    f'- Duplicates found: {duplicates_found}\n'
                    f'- Duplicates deleted: {deleted_count}\n'
                    f'- Relationships transferred: {relationships_transferred}\n'
                    f'- Total streams remaining: {AcademicStream.objects.count()}'
                )
            )
        elif dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDry run completed!\n'
                    f'- Duplicates found: {duplicates_found}\n'
                    f'- Would delete: {len(streams_to_delete)} streams\n'
                    f'- Current total streams: {AcademicStream.objects.count()}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nNo duplicates found!\n'
                    f'- Total streams: {AcademicStream.objects.count()}'
                )
            )
