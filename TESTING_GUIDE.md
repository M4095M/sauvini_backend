# Testing Guide: CORS & Email Configuration

This guide helps you test the CORS and email configuration fixes.

## Quick Test Script

Run the automated test script:

```bash
cd sauvini_backend
python test_cors_email.py
```

This will check:

- ✅ CORS configuration
- ✅ Email settings
- ✅ Email service validation
- ✅ Production deployment checklist

## Manual Testing

### 1. Test CORS Configuration Locally

#### Using curl (Recommended)

Test CORS preflight request:

```bash
curl -X OPTIONS http://localhost:8000/api/v1/auth/student/send-verification-email \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Expected Response Headers:**

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
Access-Control-Allow-Credentials: true
```

#### Test actual POST request:

```bash
curl -X POST http://localhost:8000/api/v1/auth/student/send-verification-email \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","user_type":"student"}' \
  -v
```

**Check for:**

- `Access-Control-Allow-Origin` header in response
- Status code 200 or appropriate error (not CORS error)

### 2. Test Email Configuration

#### Check Environment Variables

```bash
# In your backend directory
python manage.py shell
```

Then in the shell:

```python
from django.conf import settings

# Check email settings
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_HOST_USER: {'✅ Set' if settings.EMAIL_HOST_USER else '❌ NOT SET'}")
print(f"EMAIL_HOST_PASSWORD: {'✅ Set' if settings.EMAIL_HOST_PASSWORD else '❌ NOT SET'}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
```

#### Test Email Service Directly

```python
# In Django shell
from core.email import EmailService
from apps.users.models import User

# Get a test user
user = User.objects.first()  # or User.objects.get(email='test@example.com')

try:
    # This will validate configuration and attempt to send
    result = EmailService.send_verification_email(
        user_email=user.email,
        verification_code="123456",
        user_name="Test User",
        user_type="student"
    )
    print(f"✅ Email sent successfully: {result}")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
except Exception as e:
    print(f"❌ Email sending error: {e}")
```

### 3. Test in Production (Render)

#### Using Browser Console

1. Open your production frontend: `https://sauvini-frontend.onrender.com`
2. Open browser DevTools (F12) → Network tab
3. Try to send verification email
4. Check the request:
   - **Status**: Should be 200 or clear error message (not CORS error)
   - **Response Headers**: Look for `Access-Control-Allow-Origin`
   - **Request Headers**: Check `Origin` matches your frontend URL

#### Using curl from Terminal

Test CORS from production:

```bash
curl -X OPTIONS https://sauvini-backend.onrender.com/api/v1/auth/student/send-verification-email \
  -H "Origin: https://sauvini-frontend.onrender.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

Test actual request:

```bash
curl -X POST https://sauvini-backend.onrender.com/api/v1/auth/student/send-verification-email \
  -H "Origin: https://sauvini-frontend.onrender.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"your-test@email.com","user_type":"student"}' \
  -v
```

**Expected:**

- ✅ `Access-Control-Allow-Origin: https://sauvini-frontend.onrender.com` in response
- ✅ Status 200 (or appropriate error with CORS headers)

### 4. Test Email Configuration in Production

Check Render logs after making a request:

1. Go to Render dashboard → Your backend service → Logs
2. Look for email-related errors
3. Check for messages like:
   - ✅ "Verification email sent to..."
   - ❌ "Email configuration error: DEFAULT_FROM_EMAIL is not set"
   - ❌ "Failed to send verification email..."

## Common Issues & Solutions

### Issue: CORS Error Still Appearing

**Symptoms:**

```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**Solutions:**

1. ✅ Verify `CORS_ALLOWED_ORIGINS` includes your frontend URL
2. ✅ Check `FRONTEND_URL` is set correctly
3. ✅ Ensure `ALLOWED_HOSTS` includes backend domain
4. ✅ Redeploy backend after setting environment variables

### Issue: 500 Internal Server Error

**Symptoms:**

- Request fails with 500 status
- No CORS headers in response
- Browser shows CORS error (but it's actually a server error)

**Solutions:**

1. ✅ Check Render logs for actual error
2. ✅ Verify email configuration is set:
   - `EMAIL_HOST_USER` (Brevo SMTP key)
   - `EMAIL_HOST_PASSWORD` (Brevo SMTP password)
   - `DEFAULT_FROM_EMAIL` (verified email)
3. ✅ Test email configuration locally first

### Issue: Email Not Sending

**Symptoms:**

- Request succeeds (200 status)
- No email received
- No errors in logs

**Solutions:**

1. ✅ Check Brevo dashboard for email logs
2. ✅ Verify sender email is verified in Brevo
3. ✅ Check spam folder
4. ✅ Verify `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` settings

## Production Environment Variables Checklist

Make sure these are set in Render:

```bash
# CORS Configuration
ALLOWED_HOSTS=sauvini-backend.onrender.com,*.onrender.com
FRONTEND_URL=https://sauvini-frontend.onrender.com
CORS_ALLOWED_ORIGINS=https://sauvini-frontend.onrender.com

# Email Configuration (Brevo)
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<your-brevo-smtp-key>
EMAIL_HOST_PASSWORD=<your-brevo-smtp-password>
DEFAULT_FROM_EMAIL=<your-verified-email@domain.com>
```

## Automated Testing

Create a test file to run automated tests:

```bash
# Run the test script
python test_cors_email.py

# Or run Django tests (if you create test cases)
python manage.py test apps.authentication.tests
```

## Testing Checklist

- [ ] Run `test_cors_email.py` script
- [ ] Test CORS with curl locally
- [ ] Test email configuration locally
- [ ] Set all production environment variables
- [ ] Redeploy backend
- [ ] Test from production frontend
- [ ] Check Render logs for errors
- [ ] Verify email is received
- [ ] Test with different browsers (Chrome, Firefox, Safari)

## Need Help?

If issues persist:

1. Check Render logs
2. Check browser console for errors
3. Check Network tab for request/response details
4. Verify all environment variables are set correctly
5. Test email configuration with a simple script first
