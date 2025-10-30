"""
Health check views matching Rust backend
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
import time


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint matching Rust HealthHandler::health_check"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check') == 'ok'
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'working' if cache_status else 'error',
            'timestamp': time.time()
        }, status=200)
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness(request):
    """Liveness check endpoint matching Rust HealthHandler::liveness"""
    return Response({
        'status': 'alive',
        'timestamp': time.time()
    }, status=200)
