"""
Custom middleware for timing and logging
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TimingMiddleware(MiddlewareMixin):
    """Middleware to log request timing"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")
        return response
