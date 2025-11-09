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


def async_send_export_approved(user_email, export_type, download_url):
    """
    Convenience function to send export approval notification with download link.
    
    Args:
        user_email (str): User's email address
        export_type (str): Type of export approved
        download_url (str): Full URL to download the export
    
    Returns:
        None (email sends in background)
    """
    subject = 'Export Request Approved - Ready for Download'
    message = f'Your {export_type} export request has been approved and is ready for download.\n\nDownload Link: {download_url}'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    ✓ Export Approved
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Good news! Your export is ready.
                                </h2>
                                
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Your <strong>{export_type}</strong> export request has been approved and is now ready for download.
                                </p>
                                
                                <!-- Download Button -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                    <tr>
                                        <td align="center">
                                            <a href="{download_url}" style="display: inline-block; padding: 15px 40px; background-color: #10b981; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: bold; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);">
                                                Download Export
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #10b981; color: #065f46; font-size: 14px; line-height: 1.5;">
                                    <strong>Note:</strong> This download link will expire after use or within 24 hours for security purposes.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                    This is an automated notification from UESOPMIS<br>
                                    Please do not reply to this email
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
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
    message = f'Your {export_type} export request has been rejected.'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    Export Request Rejected
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Your <strong>{export_type}</strong> export request has been rejected by an administrator.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                    This is an automated notification from UESOPMIS<br>
                                    Please do not reply to this email
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )


def async_send_password_reset_code(user_email, reset_code):
    """
    Send password reset code email with HTML formatting.
    
    Args:
        user_email (str): User's email address
        reset_code (str): 6-digit password reset code
    
    Returns:
        None (email sends in background)
    """
    subject = 'Password Reset Code - UESOPMIS'
    message = f'Your password reset code is: {reset_code}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, please ignore this email.'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    🔐 Password Reset
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Your Password Reset Code
                                </h2>
                                
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Enter this code to reset your password:
                                </p>
                                
                                <!-- Code Display -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
                                    <tr>
                                        <td align="center">
                                            <div style="display: inline-block; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px 40px; border-radius: 8px; border: 2px dashed #3b82f6;">
                                                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1e40af; font-family: 'Courier New', monospace;">
                                                    {reset_code}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; font-size: 14px; line-height: 1.5;">
                                    <strong>⏱️ This code expires in 10 minutes</strong><br>
                                    If you didn't request this password reset, please ignore this email or contact support if you have concerns.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                    This is an automated notification from UESOPMIS<br>
                                    Please do not reply to this email
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )


def async_send_account_activated(user_email, user_name, activated_by):
    """
    Send account activation notification email.
    
    Args:
        user_email (str): User's email address
        user_name (str): User's full name
        activated_by (str): Name of person who activated the account
    
    Returns:
        None (email sends in background)
    """
    subject = 'Your Account Has Been Activated - UESOPMIS'
    message = f'Hello {user_name},\n\nYour account has been activated. You now have full access to the UESOPMIS system.'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    🎉 Account Activated
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Hello {user_name},
                                </h2>
                                
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Great news! Your account has been <strong>activated</strong>.
                                </p>
                                
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    You now have full access to all features of the UESOPMIS system.
                                </p>
                                
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #10b981; color: #065f46; font-size: 14px; line-height: 1.5;">
                                    <strong>✓ Your account is now active</strong><br>
                                    You can log in and use all system features without restrictions.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                    This is an automated notification from UESOPMIS<br>
                                    Please do not reply to this email
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )


def async_send_account_deactivated(user_email, user_name, deactivated_by):
    """
    Send account deactivation notification email.
    
    Args:
        user_email (str): User's email address
        user_name (str): User's full name
        deactivated_by (str): Name of person who deactivated the account
    
    Returns:
        None (email sends in background)
    """
    subject = 'Your Account Has Been Deactivated - UESOPMIS'
    message = f'Hello {user_name},\n\nYour account has been deactivated. Your access to the UESOPMIS system has been restricted.'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    Account Deactivated
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Hello {user_name},
                                </h2>
                                
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Your account has been <strong>deactivated</strong>.
                                </p>
                                
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Your access to the UESOPMIS system has been restricted.
                                </p>
                                
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; font-size: 14px; line-height: 1.5;">
                                    <strong>⚠️ Account Status: Deactivated</strong><br>
                                    If you believe this is a mistake or have questions, please contact the administrator immediately.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                    This is an automated notification from UESOPMIS<br>
                                    Please do not reply to this email
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )


def async_send_email_changed(user_email, user_name, old_email, new_email):
    """
    Send email change notification to both old and new email addresses.
    
    Args:
        user_email (str): Email address to send to (can be old or new)
        user_name (str): User's full name
        old_email (str): Previous email address
        new_email (str): New email address
    
    Returns:
        None (email sends in background)
    """
    subject = 'Email Address Changed - UESOPMIS'
    message = f'Hello {user_name},\n\nYour email address has been changed from {old_email} to {new_email}.'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    📧 Email Changed
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Hello {user_name},
                                </h2>
                                
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Your email address has been successfully changed.
                                </p>
                                
                                <table width="100%" cellpadding="10" cellspacing="0" style="margin: 20px 0; border: 1px solid #e5e7eb; border-radius: 6px;">
                                    <tr>
                                        <td style="background-color: #f9fafb; color: #6b7280; font-size: 14px; font-weight: bold; width: 120px;">
                                            Previous Email:
                                        </td>
                                        <td style="color: #4b5563; font-size: 14px;">
                                            {old_email}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="background-color: #f9fafb; color: #6b7280; font-size: 14px; font-weight: bold;">
                                            New Email:
                                        </td>
                                        <td style="color: #1f2937; font-size: 14px; font-weight: bold;">
                                            {new_email}
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #fef2f2; border-left: 4px solid #ef4444; color: #991b1b; font-size: 14px; line-height: 1.5;">
                                    <strong>⚠️ Security Notice</strong><br>
                                    If you did not make this change, please contact support immediately as your account may have been compromised.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">
                                    This is an automated notification from UESOPMIS<br>
                                    Please do not reply to this email
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''
    
    async_send_mail(
        subject=subject,
        message=message,
        recipient_list=[user_email],
        html_message=html_message
    )