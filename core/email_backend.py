"""
Custom SMTP email backend with proper timeout support
"""
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings


class TimeoutSMTPBackend(EmailBackend):
    """SMTP backend with configurable timeout to prevent worker timeout"""
    
    def __init__(self, fail_silently=False, **kwargs):
        # Get timeout from settings (default 10 seconds)
        timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
        kwargs.setdefault('timeout', timeout)
        super().__init__(fail_silently=fail_silently, **kwargs)

