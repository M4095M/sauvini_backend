"""
URL configuration for lives app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Live endpoints
    path('lives', views.lives_list_create, name='lives_list_create'),
    path('lives/<uuid:live_id>', views.live_detail, name='live_detail'),
    path('lives/<uuid:live_id>/cancel', views.cancel_live, name='cancel_live'),
    path('lives/<uuid:live_id>/start', views.start_live, name='start_live'),
    path('lives/<uuid:live_id>/end', views.end_live, name='end_live'),
    path('lives/<uuid:live_id>/comments', views.live_comments, name='live_comments'),
]

