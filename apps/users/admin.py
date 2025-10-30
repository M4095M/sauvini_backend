from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Professor, Admin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'wilaya', 'academic_stream', 'email_verified', 'created_at')
    list_filter = ('wilaya', 'academic_stream', 'email_verified', 'created_at')
    search_fields = ('first_name', 'last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def email(self, obj):
        return obj.user.email


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'wilaya', 'status', 'email_verified', 'created_at')
    list_filter = ('wilaya', 'status', 'email_verified', 'created_at')
    search_fields = ('first_name', 'last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def email(self, obj):
        return obj.user.email


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    
    def email(self, obj):
        return obj.user.email