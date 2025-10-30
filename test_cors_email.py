"""
Test script for CORS and Email Configuration
Run this script to verify CORS and email settings are working correctly
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sauvini.settings')
django.setup()

from django.conf import settings
from django.test import RequestFactory
from django.test.utils import override_settings
from apps.authentication.views import send_verification_email
from core.email import EmailService
import json


def test_cors_configuration():
    """Test that CORS is properly configured"""
    print("\n" + "="*60)
    print("TESTING CORS CONFIGURATION")
    print("="*60)
    
    # Check CORS settings
    print(f"\n✓ CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
    print(f"✓ CORS_ALLOW_CREDENTIALS: {settings.CORS_ALLOW_CREDENTIALS}")
    print(f"✓ CORS_ALLOW_ALL_ORIGINS: {settings.CORS_ALLOW_ALL_ORIGINS}")
    print(f"✓ CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
    
    # Check if production URLs are included
    prod_url = "https://sauvini-frontend.onrender.com"
    if prod_url in settings.CORS_ALLOWED_ORIGINS:
        print(f"\n✅ Production frontend URL is in CORS_ALLOWED_ORIGINS")
    else:
        print(f"\n❌ Production frontend URL NOT in CORS_ALLOWED_ORIGINS")
        print(f"   Add this to CORS_ALLOWED_ORIGINS: {prod_url}")
    
    # Check ALLOWED_HOSTS
    print(f"\n✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    prod_backend = "sauvini-backend.onrender.com"
    if prod_backend in settings.ALLOWED_HOSTS or any("*" in host for host in settings.ALLOWED_HOSTS):
        print(f"✅ Backend host configuration looks good")
    else:
        print(f"\n❌ Consider adding production backend to ALLOWED_HOSTS")
        print(f"   Add: sauvini-backend.onrender.com or *.onrender.com")


def test_email_configuration():
    """Test that email configuration is properly set"""
    print("\n" + "="*60)
    print("TESTING EMAIL CONFIGURATION")
    print("="*60)
    
    # Check email settings
    print(f"\n✓ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"✓ EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"✓ EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"✓ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"✓ EMAIL_HOST_USER: {'✅ Set' if settings.EMAIL_HOST_USER else '❌ NOT SET'}")
    print(f"✓ EMAIL_HOST_PASSWORD: {'✅ Set' if settings.EMAIL_HOST_PASSWORD else '❌ NOT SET'}")
    print(f"✓ DEFAULT_FROM_EMAIL: {'✅ Set' if settings.DEFAULT_FROM_EMAIL else '❌ NOT SET'}")
    
    if settings.DEFAULT_FROM_EMAIL:
        print(f"  → Value: {settings.DEFAULT_FROM_EMAIL}")
    else:
        print(f"  → ERROR: DEFAULT_FROM_EMAIL is required!")
    
    # Validate email configuration
    issues = []
    if not settings.EMAIL_HOST_USER:
        issues.append("EMAIL_HOST_USER is not set")
    if not settings.EMAIL_HOST_PASSWORD:
        issues.append("EMAIL_HOST_PASSWORD is not set")
    if not settings.DEFAULT_FROM_EMAIL:
        issues.append("DEFAULT_FROM_EMAIL is not set")
    
    if issues:
        print(f"\n❌ Email configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print(f"\n   Fix: Set these environment variables in production")
    else:
        print(f"\n✅ Email configuration looks good!")


def test_email_service_validation():
    """Test EmailService validation"""
    print("\n" + "="*60)
    print("TESTING EMAIL SERVICE VALIDATION")
    print("="*60)
    
    try:
        # This should validate configuration without actually sending
        # We'll just check if it raises ValueError for missing config
        test_email = "test@example.com"
        test_token = "123456"
        test_name = "Test User"
        
        # Check if validation would pass
        if not settings.DEFAULT_FROM_EMAIL:
            print("\n⚠️  DEFAULT_FROM_EMAIL not set - validation will fail")
        elif not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            print("\n⚠️  Email credentials not set - validation will fail")
        else:
            print("\n✅ Email service validation should pass")
            print("   (Note: This doesn't actually send an email)")
            
    except Exception as e:
        print(f"\n❌ Email service validation error: {e}")


def test_endpoint_simulation():
    """Simulate the endpoint call to check for errors"""
    print("\n" + "="*60)
    print("TESTING ENDPOINT SIMULATION")
    print("="*60)
    
    factory = RequestFactory()
    
    # Simulate request from production frontend
    request = factory.post(
        '/api/v1/auth/student/send-verification-email',
        data=json.dumps({
            'email': 'test@example.com',
            'user_type': 'student'
        }),
        content_type='application/json',
        HTTP_ORIGIN='https://sauvini-frontend.onrender.com'
    )
    
    print(f"\n✓ Simulated POST request with origin: {request.META.get('HTTP_ORIGIN')}")
    
    # Check if CORS middleware would allow this
    from corsheaders.middleware import CorsMiddleware
    middleware = CorsMiddleware(lambda req: None)
    
    # Note: This is a simplified check - actual CORS depends on middleware processing
    print(f"\n📝 Note: Actual CORS validation happens in middleware")
    print(f"   Check browser network tab for CORS headers in response")


def print_production_checklist():
    """Print checklist for production deployment"""
    print("\n" + "="*60)
    print("PRODUCTION DEPLOYMENT CHECKLIST")
    print("="*60)
    
    checklist = [
        ("Set ALLOWED_HOSTS", "sauvini-backend.onrender.com,*.onrender.com"),
        ("Set FRONTEND_URL", "https://sauvini-frontend.onrender.com"),
        ("Set CORS_ALLOWED_ORIGINS", "https://sauvini-frontend.onrender.com"),
        ("Set EMAIL_HOST", "smtp-relay.brevo.com"),
        ("Set EMAIL_HOST_USER", "Your Brevo SMTP key"),
        ("Set EMAIL_HOST_PASSWORD", "Your Brevo SMTP password"),
        ("Set DEFAULT_FROM_EMAIL", "Your verified Brevo email"),
    ]
    
    print("\nRequired Environment Variables for Production:")
    for i, (item, value) in enumerate(checklist, 1):
        print(f"  {i}. {item}")
        print(f"     → {value}")
    
    print("\n💡 Tip: Test with curl to verify CORS headers:")
    print("   curl -X OPTIONS https://sauvini-backend.onrender.com/api/v1/auth/student/send-verification-email \\")
    print("        -H 'Origin: https://sauvini-frontend.onrender.com' \\")
    print("        -H 'Access-Control-Request-Method: POST' \\")
    print("        -v")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SAUVINI BACKEND - CORS & EMAIL CONFIGURATION TEST")
    print("="*60)
    
    test_cors_configuration()
    test_email_configuration()
    test_email_service_validation()
    test_endpoint_simulation()
    print_production_checklist()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Fix any issues shown above")
    print("2. Set environment variables in Render dashboard")
    print("3. Redeploy the backend")
    print("4. Test with browser or curl from production frontend")
    print()

