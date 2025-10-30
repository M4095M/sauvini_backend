from django.contrib import admin
from .models import Live, LiveComment


@admin.register(Live)
class LiveAdmin(admin.ModelAdmin):
    list_display = ['title', 'professor', 'status', 'scheduled_datetime', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'professor__first_name', 'professor__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(LiveComment)
class LiveCommentAdmin(admin.ModelAdmin):
    list_display = ['live', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

