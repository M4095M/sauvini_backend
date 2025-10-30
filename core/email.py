"""
Email service utilities
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging
import random
import string

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending various types of emails"""
    
    @staticmethod
    def generate_verification_code(length=6):
        """Generate a random verification code"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def generate_verification_email_html(user_name: str, token: str) -> str:
        """Generate HTML email template for email verification with 6-digit code"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Confirmation</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background-color: #007bff;
                    color: #ffffff;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 30px;
                }}
                .token {{
                    display: block;
                    font-size: 32px;
                    font-weight: bold;
                    color: #28a745;
                    text-align: center;
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    letter-spacing: 4px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #28a745;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Sauvini Platform</h1>
                    <h2>Email Confirmation</h2>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>Thank you for registering with Sauvini! To confirm your email address, please use the following 6-digit verification code:</p>
                    
                    <div class="token">{token}</div>
                    
                    <p>Go to our email confirmation page and enter this code to verify your account:</p>
                    
                    <p><strong>Note:</strong> This code will expire in 60 minutes for security reasons. If you did not request this, please ignore this email.</p>
                    
                    <p>If you have any questions, feel free to contact our support team.</p>
                    
                    <p>Best regards,<br>The Sauvini Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2025 Sauvini. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def send_verification_email(user_email, verification_code, user_name, user_type='student'):
        """Send email verification email with 6-digit code"""
        # Validate email configuration before attempting to send
        if not settings.DEFAULT_FROM_EMAIL:
            error_msg = "Email configuration error: DEFAULT_FROM_EMAIL is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            error_msg = "Email configuration error: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            subject = 'Please confirm your email'
            
            # Generate HTML content
            html_content = EmailService.generate_verification_email_html(user_name, verification_code)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=f"Your verification code is: {verification_code}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Verification email sent to {user_email}")
            return True
        except ValueError:
            # Re-raise configuration errors
            raise
        except Exception as e:
            error_msg = f"Failed to send verification email to {user_email}: {e}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    @staticmethod
    def send_password_reset_email(user_email, reset_token, user_type='student'):
        """Send password reset email"""
        try:
            subject = 'Reset your Sauvini password'
            message = f'Please click the link to reset your password: {settings.FRONTEND_URL}/reset-password?token={reset_token}&type={user_type}'
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user_email}: {e}")
            return False
    
    @staticmethod
    def send_professor_approval_email(professor_email, approved=True):
        """Send professor approval/rejection email"""
        try:
            if approved:
                subject = 'Your professor account has been approved'
                message = 'Congratulations! Your professor account has been approved. You can now log in and start creating content.'
            else:
                subject = 'Your professor account application'
                message = 'Thank you for your interest. Unfortunately, your professor account application was not approved at this time.'
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[professor_email],
                fail_silently=False,
            )
            logger.info(f"Professor approval email sent to {professor_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send professor approval email to {professor_email}: {e}")
            return False
