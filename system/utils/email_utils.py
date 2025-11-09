"""
Asynchronous Email Utility
Provides non-blocking email sending using threading to prevent UI blocking.
"""

import threading
import logging
from django.core.mail import send_mail as django_send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def async_send_mail(subject, message, from_email=None, recipient_list=None, 
                    fail_silently=False, html_message=None, **kwargs):
    """
    Send email asynchronously in a background thread.
    
    This prevents email sending from blocking the HTTP response,
    solving the 2-minute delay issue when SMTP is slow.
    
    Args:
        subject (str): Email subject line
        message (str): Plain text email body
        from_email (str, optional): Sender email. Defaults to settings.DEFAULT_FROM_EMAIL
        recipient_list (list): List of recipient email addresses
        fail_silently (bool): If False, raises exceptions. If True, suppresses errors
        html_message (str, optional): HTML version of email body
        **kwargs: Additional arguments to pass to send_mail()
    
    Returns:
        None (email sends in background thread)
    
    Example:
        async_send_mail(
            subject='Verification Code',
            message='Your code is 123456',
            recipient_list=[user.email],
            html_message='<p>Your code is <strong>123456</strong></p>'
        )
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    if recipient_list is None:
        logger.error("async_send_mail called without recipient_list")
        return
    
    def send_email():
        """Inner function to send email in background thread."""
        try:
            django_send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
                html_message=html_message,
                **kwargs
            )
            logger.info(f"Email sent successfully to {recipient_list}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
            if not fail_silently:
                # Re-raise in background thread (will be logged but won't crash request)
                raise
    
    # Start background thread (daemon=True means thread dies when main program exits)
    thread = threading.Thread(target=send_email, daemon=True)
    thread.start()
    
    logger.debug(f"Email queued for async sending to {recipient_list}: {subject}")


def async_send_verification_code(user_email, verification_code):
    """
    Convenience function to send verification code email asynchronously.
    
    Args:
        user_email (str): User's email address
        verification_code (str): 6-digit verification code
    
    Returns:
        None (email sends in background)
    """
    subject = 'Your Verification Code'
    message = f'Your verification code is: {verification_code}\n\nThis code will expire in 10 minutes.'
    html_message = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Verification Code</h2>
        <p>Your verification code is:</p>
        <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px;">
            {verification_code}
        </div>
        <p style="color: #666; margin-top: 15px;">This code will expire in 10 minutes.</p>
    </div>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )


def async_send_export_approved(user_email, export_type):
    """
    Convenience function to send export approval notification.
    
    Args:
        user_email (str): User's email address
        export_type (str): Type of export approved
    
    Returns:
        None (email sends in background)
    """
    subject = 'Export Request Approved'
    message = f'Your {export_type} export request has been approved and is ready for download.'
    html_message = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #10b981;">Export Request Approved ✓</h2>
        <p>Your <strong>{export_type}</strong> export request has been approved.</p>
        <p>You can now download your export from the system.</p>
    </div>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )


def async_send_export_rejected(user_email, export_type):
    """
    Convenience function to send export rejection notification.
    
    Args:
        user_email (str): User's email address
        export_type (str): Type of export rejected
    
    Returns:
        None (email sends in background)
    """
    subject = 'Export Request Rejected'
    message = f'Your {export_type} export request has been rejected. Please contact support if you have questions.'
    html_message = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #ef4444;">Export Request Rejected</h2>
        <p>Your <strong>{export_type}</strong> export request has been rejected.</p>
        <p>Please contact support if you have questions or need assistance.</p>
    </div>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )
