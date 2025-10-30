# Generated manually for Lives app

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0002_alter_professor_cv_path'),
        ('courses', '0007_add_file_references_to_lesson'),
        ('files', '0002_alter_fileuploadsession_upload_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='Live',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('scheduled_datetime', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Live', 'Live'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled')], default='Pending', max_length=20)),
                ('recording_url', models.URLField(blank=True, max_length=500, null=True)),
                ('viewer_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_streams', models.ManyToManyField(blank=True, related_name='lives', to='courses.academicstream')),
                ('chapter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lives', to='courses.chapter')),
                ('module', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lives', to='courses.module')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lives', to='users.professor')),
                ('recording_file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='live_recordings', to='files.file')),
            ],
            options={
                'db_table': 'lives',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LiveComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('live', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='lives.live')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='live_comments', to='users.user')),
            ],
            options={
                'db_table': 'live_comments',
                'ordering': ['created_at'],
            },
        ),
    ]

