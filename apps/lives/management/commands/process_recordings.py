"""
Management command to process Jitsi recordings from Docker volume and upload to MinIO

Usage:
    python manage.py process_recordings [--jibri-volume-path=/path/to/recordings]
"""
import os
import glob
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.lives.models import Live, LiveStatus
from apps.lives.services import upload_recording_to_minio

class Command(BaseCommand):
    help = 'Process Jitsi recordings from Docker volume and upload to MinIO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jibri-volume-path',
            type=str,
            default=None,
            help='Path to Jibri recordings directory (default: auto-detect or Docker volume)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without uploading',
        )

    def handle(self, *args, **options):
        jibri_path = options['jibri_volume_path']
        dry_run = options['dry_run']

        # Default paths to check
        default_paths = [
            '/var/lib/docker/volumes/jitsi_jibri-recordings/_data',  # Docker volume path
            '/recordings',  # Inside Jibri container
            './jitsi/recordings',  # Local development
        ]

        if jibri_path:
            recording_paths = [jibri_path]
        else:
            recording_paths = default_paths

        # Find recordings directory
        recordings_dir = None
        for path in recording_paths:
            if os.path.exists(path) and os.path.isdir(path):
                recordings_dir = path
                self.stdout.write(self.style.SUCCESS(f'Found recordings directory: {path}'))
                break

        if not recordings_dir:
            self.stdout.write(
                self.style.ERROR(
                    'Could not find recordings directory. Please specify --jibri-volume-path'
                )
            )
            return

        # Find all MP4 files (Jitsi recordings)
        video_extensions = ['*.mp4', '*.mkv', '*.webm']
        recording_files = []
        for ext in video_extensions:
            recording_files.extend(glob.glob(os.path.join(recordings_dir, ext)))
            recording_files.extend(glob.glob(os.path.join(recordings_dir, '**', ext), recursive=True))

        if not recording_files:
            self.stdout.write(self.style.WARNING('No recording files found'))
            return

        self.stdout.write(f'Found {len(recording_files)} recording file(s)')

        # Process each recording
        processed = 0
        skipped = 0
        errors = 0

        for recording_path in recording_files:
            filename = os.path.basename(recording_path)
            self.stdout.write(f'Processing: {filename}')

            # Try to match recording to a live session
            # Jitsi recordings are named: {room_name}-{timestamp}.mp4
            # Our room names are: sauvini-live-{live_id}
            live = None
            if 'sauvini-live-' in filename:
                # Extract room name part
                room_part = filename.split('-')[0:3]  # sauvini-live-{id}
                if len(room_part) >= 3:
                    room_id_part = room_part[2].replace('.mp4', '').replace('.mkv', '').replace('.webm', '')
                    # Try to find matching live session
                    try:
                        # Search for lives that match this room pattern
                        # Room name format: sauvini-live-{uuid_without_dashes}
                        from apps.lives.models import Live
                        all_lives = Live.objects.filter(
                            status__in=[LiveStatus.ENDED, LiveStatus.LIVE],
                            ended_at__isnull=False
                        ).order_by('-ended_at')

                        # Try to match by room name or time proximity
                        for l in all_lives:
                            if l.jitsi_room_name:
                                room_name_without_prefix = l.jitsi_room_name.replace('sauvini-live-', '')
                                if room_id_part in room_name_without_prefix or room_name_without_prefix in room_id_part:
                                    # Check if recording time is close to ended_at time
                                    file_mod_time = os.path.getmtime(recording_path)
                                    file_mod_datetime = timezone.datetime.fromtimestamp(file_mod_time, tz=timezone.utc)
                                    
                                    if l.ended_at:
                                        time_diff = abs((file_mod_datetime - l.ended_at).total_seconds())
                                        if time_diff < 3600:  # Within 1 hour
                                            live = l
                                            break

                        if not live:
                            # If no match found, try the most recent ended live without recording
                            live = Live.objects.filter(
                                status=LiveStatus.ENDED,
                                ended_at__isnull=False,
                                recording_file__isnull=True
                            ).order_by('-ended_at').first()

                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Error matching recording to live: {e}')
                        )

            # If still no match, use most recent ended live without recording
            if not live:
                live = Live.objects.filter(
                    status=LiveStatus.ENDED,
                    ended_at__isnull=False,
                    recording_file__isnull=True
                ).order_by('-ended_at').first()

            if not live:
                self.stdout.write(
                    self.style.WARNING(f'Could not match {filename} to a live session. Skipping.')
                )
                skipped += 1
                continue

            if live.recording_file:
                self.stdout.write(
                    self.style.WARNING(f'Live {live.id} already has a recording. Skipping.')
                )
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[DRY RUN] Would upload {filename} to live {live.id} ({live.title})'
                    )
                )
                processed += 1
                continue

            # Upload recording
            try:
                file_obj = upload_recording_to_minio(live, recording_path, filename)
                if file_obj:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Uploaded {filename} to live {live.id} ({live.title})'
                        )
                    )
                    processed += 1
                    
                    # Optionally remove the local file after successful upload
                    # Uncomment to enable:
                    # os.remove(recording_path)
                    # self.stdout.write(f'  Removed local file: {recording_path}')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to upload {filename}')
                    )
                    errors += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {filename}: {e}')
                )
                errors += 1

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Processing Summary:'))
        self.stdout.write(f'  Processed: {processed}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Errors: {errors}')
        self.stdout.write(self.style.SUCCESS('=' * 50))

