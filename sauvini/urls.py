"""
URL configuration for sauvini project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API v1 routes
    path('api/v1/', include('apps.authentication.urls')),
    path('api/v1/courses/', include('apps.courses.urls')),
    path('api/v1/progress/', include('apps.progress.urls')),
    path('api/v1/', include('apps.files.urls')),
    path('api/v1/assessments/', include('apps.assessments.urls')),
    path('api/v1/exams/', include('apps.assessments.exam_urls')),  # Direct route for exams
    path('api/v1/', include('apps.purchases.urls')),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.lives.urls')),
    
    # Health check endpoints
    path('health/', include('apps.authentication.urls')),  # Will add health check later
]
