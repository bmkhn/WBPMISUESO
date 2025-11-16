"""
Asynchronous Email Utility
Provides non-blocking email sending using threading to prevent UI blocking.
Now using SendGrid API for reliable delivery on cloud platforms.
"""

import threading
import logging
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


def async_send_mail(subject, message, from_email=None, recipient_list=None, 
                    fail_silently=False, html_message=None, **kwargs):
    """
    Send email asynchronously using SendGrid API in a background thread.
    
    This prevents email sending from blocking the HTTP response,
    solving the 2-minute delay issue when SMTP is slow.
    
    Args:
        subject (str): Email subject line
        message (str): Plain text email body
        from_email (str, optional): Sender email. Defaults to settings.DEFAULT_FROM_EMAIL
        recipient_list (list): List of recipient email addresses
        fail_silently (bool): If False, raises exceptions. If True, suppresses errors
        html_message (str, optional): HTML version of email body
        **kwargs: Additional arguments (for compatibility)
    
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
        from_email = settings.SENDGRID_FROM_EMAIL
    
    if recipient_list is None:
        logger.error("async_send_mail called without recipient_list")
        return
    
    def send_email():
        """Inner function to send email via SendGrid API in background thread."""
        try:
            # Create SendGrid message
            sg_message = Mail(
                from_email=Email(from_email),
                to_emails=[To(email) for email in recipient_list],
                subject=subject,
                plain_text_content=Content("text/plain", message)
            )
            
            # Add HTML content if provided
            if html_message:
                sg_message.add_content(Content("text/html", html_message))
            
            # Send via SendGrid API
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(sg_message)
            
            logger.info(f"Email sent successfully via SendGrid to {recipient_list}: {subject} (status: {response.status_code})")
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid to {recipient_list}: {str(e)}")
            if not fail_silently:
                # Re-raise in background thread (will be logged but won't crash request)
                raise
    
    # Start background thread (daemon=True means thread dies when main program exits)
    thread = threading.Thread(target=send_email, daemon=True)
    thread.start()
    
    logger.debug(f"Email queued for async SendGrid delivery to {recipient_list}: {subject}")


def async_send_verification_code(user_email, verification_code):
    """
    Convenience function to send verification code email asynchronously.
    
    Args:
        user_email (str): User's email address
        verification_code (str): 6-digit verification code
    
    Returns:
        None (email sends in background)
    """
    subject = 'Your Verification Code - UESOPMIS'
    message = f'Your verification code is: {verification_code}\n\nThis code will expire in 10 minutes.'
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
                                    ✓ Verification Code
                                </h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Welcome to UESOPMIS!
                                </h2>
                                
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    To complete your registration, please enter the verification code below:
                                </p>
                                
                                <!-- Code Display -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                    <tr>
                                        <td align="center">
                                            <div style="display: inline-block; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 25px 50px; border-radius: 12px; border: 3px solid #10b981; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);">
                                                <span style="font-size: 36px; font-weight: bold; letter-spacing: 10px; color: #065f46; font-family: 'Courier New', monospace;">
                                                    {verification_code}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; font-size: 14px; line-height: 1.5;">
                                    <strong>⏱️ This code expires in 10 minutes</strong><br>
                                    For security reasons, do not share this code with anyone.
                                </p>
                                
                                <p style="margin: 20px 0 0 0; color: #6b7280; font-size: 14px; line-height: 1.5; text-align: center;">
                                    If you didn't request this code, you can safely ignore this email.
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


def async_send_password_changed(user_email, user_name, new_password):
    """
    Send password change notification email with the new password.
    
    Args:
        user_email (str): User's email address
        user_name (str): User's full name
        new_password (str): The new password that was set
    
    Returns:
        None (email sends in background)
    """
    subject = 'Password Changed Successfully - UESOPMIS'
    message = f'Hello {user_name},\n\nYour password has been changed successfully.\n\nYour new password is: {new_password}\n\nIf you did not make this change, please contact support immediately.'
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">🔒 Password Changed</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">Hello {user_name},</h2>
                                <p style="margin: 0 0 15px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">This email confirms that your password has been <strong>successfully changed</strong>.</p>
                                
                                <p style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 3px solid #10b981; border-radius: 12px; text-align: center;">
                                    <strong style="color: #065f46; font-size: 14px; display: block; margin-bottom: 10px;">Your New Password:</strong>
                                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 2px; color: #047857; font-family: 'Courier New', monospace; display: block;">{new_password}</span>
                                </p>
                                
                                <p style="margin: 0 0 20px 0; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #10b981; color: #065f46; font-size: 14px; line-height: 1.5;"><strong>✓ Password Updated</strong><br>Your account is now secured with your new password. You can use it to log in immediately.</p>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #fef2f2; border-left: 4px solid #ef4444; color: #991b1b; font-size: 14px; line-height: 1.5;"><strong>⚠️ Security Alert</strong><br>If you did not make this change, your account may have been compromised. Please contact support immediately and reset your password.</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px;">This is an automated notification from UESOPMIS<br>Please do not reply to this email</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''
    async_send_mail(subject=subject, message=message, recipient_list=[user_email], html_message=html_message)


def async_send_password_change_verification(user_email, verification_code):
    """Send verification code for password change in profile."""
    subject = 'Verify Password Change - UESOPMIS'
    message = f'Your password change verification code is: {verification_code}\n\nThis code will expire in 10 minutes.'
    html_message = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr><td style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px 40px; text-align: center;"><h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">🔐 Verify Password Change</h1></td></tr>
                    <tr><td style="padding: 40px;">
                        <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">Confirm Your Password Change</h2>
                        <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">You've requested to change your password. To confirm this change, please enter the verification code below:</p>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;"><tr><td align="center">
                            <div style="display: inline-block; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); padding: 25px 50px; border-radius: 12px; border: 3px solid #f59e0b; box-shadow: 0 4px 6px rgba(245, 158, 11, 0.2);">
                                <span style="font-size: 36px; font-weight: bold; letter-spacing: 10px; color: #92400e; font-family: 'Courier New', monospace;">{verification_code}</span>
                            </div>
                        </td></tr></table>
                        <p style="margin: 20px 0 0 0; padding: 15px; background-color: #fffbeb; border-left: 4px solid #f59e0b; color: #92400e; font-size: 14px; line-height: 1.5;"><strong>⏱️ This code expires in 10 minutes</strong><br>If you didn't request this password change, please ignore this email or contact support if you have concerns.</p>
                    </td></tr>
                    <tr><td style="background-color: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;"><p style="margin: 0; color: #6b7280; font-size: 12px;">This is an automated notification from UESOPMIS<br>Please do not reply to this email</p></td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    '''
    async_send_mail(subject=subject, message=message, recipient_list=[user_email], html_message=html_message)


def async_send_meeting_event_added(recipient_emails, meeting_event):
    """
    Send email when a user is added to a meeting event.
    
    Args:
        recipient_emails (list): List of participant email addresses
        meeting_event: MeetingEvent instance
    """
    from django.utils.dateformat import format as date_format
    
    event_datetime = date_format(meeting_event.datetime, 'F d, Y \a\t g:i A')
    
    subject = f'You have been added to: {meeting_event.title}'
    message = f'You have been added as a participant to the meeting "{meeting_event.title}" scheduled for {event_datetime}.'
    
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    📅 New Meeting Invitation
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    You've been added to a meeting
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    You have been added as a participant to the following meeting:
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 20px; background-color: #f9fafb;">
                                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 18px;">
                                                {meeting_event.title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📅 Date & Time:</strong> {event_datetime}
                                            </p>
                                            {f'<p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;"><strong>📍 Location:</strong> {meeting_event.location}</p>' if meeting_event.location else ''}
                                            {f'<p style="margin: 0; color: #4b5563; font-size: 14px;"><strong>📝 Description:</strong> {meeting_event.description}</p>' if meeting_event.description else ''}
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #dbeafe; border-left: 4px solid #3b82f6; color: #1e40af; font-size: 14px; line-height: 1.5;">
                                    <strong>ℹ️ Save the Date</strong><br>
                                    Please mark your calendar for this meeting. You will receive reminder emails as the date approaches.
                                </p>
                            </td>
                        </tr>
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
        recipient_list=recipient_emails,
        html_message=html_message
    )


def async_send_project_event_added(recipient_emails, project_event):
    """
    Send email when a project event (activity) is created for project members.
    
    Args:
        recipient_emails (list): List of project team member email addresses
        project_event: ProjectEvent instance
    """
    from django.utils.dateformat import format as date_format
    
    event_datetime = date_format(project_event.datetime, 'F d, Y \a\t g:i A') if project_event.datetime else 'TBD'
    
    subject = f'New Activity Added: {project_event.title}'
    message = f'A new activity "{project_event.title}" has been added to the project "{project_event.project.title}" scheduled for {event_datetime}.'
    
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    🎯 New Project Activity
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    New activity scheduled for your project
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    A new activity has been added to your project:
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 20px; background-color: #f9fafb;">
                                            <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                                                <strong>Project</strong>
                                            </p>
                                            <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 16px;">
                                                {project_event.project.title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                                                <strong>Activity</strong>
                                            </p>
                                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 18px;">
                                                {project_event.title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📅 Date & Time:</strong> {event_datetime}
                                            </p>
                                            {f'<p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;"><strong>📍 Location:</strong> {project_event.location}</p>' if project_event.location else ''}
                                            {f'<p style="margin: 0; color: #4b5563; font-size: 14px;"><strong>📝 Description:</strong> {project_event.description}</p>' if project_event.description else ''}
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #f3e8ff; border-left: 4px solid #8b5cf6; color: #5b21b6; font-size: 14px; line-height: 1.5;">
                                    <strong>ℹ️ Mark Your Calendar</strong><br>
                                    Please prepare for this activity. You will receive reminder emails as the date approaches.
                                </p>
                            </td>
                        </tr>
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
        recipient_list=recipient_emails,
        html_message=html_message
    )


def async_send_event_reminder(recipient_emails, event_title, event_datetime, event_location, event_description, event_type='meeting', days_before=None):
    """
    Send event reminder email to participants.
    
    Args:
        recipient_emails (list): List of participant email addresses
        event_title (str): Title of the event
        event_datetime (datetime): Event datetime
        event_location (str): Event location
        event_description (str): Event description
        event_type (str): 'meeting' or 'activity'
        days_before (int): Number of days before event (None for day-of reminder)
    """
    from django.utils.dateformat import format as date_format
    
    event_datetime_str = date_format(event_datetime, 'F d, Y \a\t g:i A')
    
    if days_before:
        reminder_type = f'{days_before} Days Before'
        subject = f'Reminder: {event_title} in {days_before} days'
        message_intro = f'This is a reminder that you have a {event_type} coming up in {days_before} days.'
        emoji = '⏰'
        color = '#f59e0b'
        bg_color = '#fffbeb'
        border_color = '#f59e0b'
        text_color = '#92400e'
    else:
        reminder_type = 'Today'
        subject = f'Today: {event_title}'
        message_intro = f'This is a reminder that your {event_type} is scheduled for today.'
        emoji = '🔔'
        color = '#ef4444'
        bg_color = '#fef2f2'
        border_color = '#ef4444'
        text_color = '#991b1b'
    
    message = f'{message_intro}\n\nEvent: {event_title}\nDate & Time: {event_datetime_str}\nLocation: {event_location or "TBD"}'
    
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
                        <tr>
                            <td style="background: linear-gradient(135deg, {color} 0%, {color} 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    {emoji} Event Reminder
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    {reminder_type} Reminder
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    {message_intro}
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 20px; background-color: #f9fafb;">
                                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 18px;">
                                                {event_title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📅 Date & Time:</strong> {event_datetime_str}
                                            </p>
                                            {f'<p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;"><strong>📍 Location:</strong> {event_location}</p>' if event_location else ''}
                                            {f'<p style="margin: 0; color: #4b5563; font-size: 14px;"><strong>📝 Description:</strong> {event_description}</p>' if event_description else ''}
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: {bg_color}; border-left: 4px solid {border_color}; color: {text_color}; font-size: 14px; line-height: 1.5;">
                                    <strong>📌 Don't Forget</strong><br>
                                    Please make sure you're prepared and available for this event.
                                </p>
                            </td>
                        </tr>
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
        recipient_list=recipient_emails,
        html_message=html_message
    )

def async_send_added_to_project(recipient_email, project, role='provider'):
    """
    Send email when a user is added to a project.

    Args:
        recipient_email (str): Email address of the user being added
        project: Project instance
        role (str): 'leader' or 'provider'
    """
    from django.utils.dateformat import format as date_format
    
    role_display = 'Project Leader' if role == 'leader' else 'Project Provider'
    start_date = date_format(project.start_date, 'F d, Y')
    end_date = date_format(project.estimated_end_date, 'F d, Y')
    
    subject = "You have been added to project: $(){project.title}"
    message = "You have been added to the project \"{project.title}\" as {role_display}.\n\nProject Period: {start_date} - {end_date}"
    
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                     Added to Project
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    You've been added to a project
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    You have been assigned to the following project as <strong>{role_display}</strong>:
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 20px; background-color: #f9fafb;">
                                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 18px;">
                                                {project.title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong> Type:</strong> {project.get_project_type_display()}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong> Start Date:</strong> {start_date}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong> End Date:</strong> {end_date}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong> Location:</strong> {project.primary_location}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong> Beneficiary:</strong> {project.primary_beneficiary}
                                            </p>
                                            <p style="margin: 0; color: #4b5563; font-size: 14px;">
                                                <strong> Events:</strong> {project.estimated_events} planned event(s)
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #10b981; color: #065f46; font-size: 14px; line-height: 1.5;">
                                    <strong> Welcome to the Team!</strong><br>
                                    You can now access this project in your dashboard and collaborate with other team members.
                                </p>
                            </td>
                        </tr>
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
        recipient_list=[recipient_email],
        html_message=html_message
    )


def async_send_added_to_project(recipient_email, project, role='provider'):
    """
    Send email when a user is added to a project.
    
    Args:
        recipient_email (str): Email address of the user being added
        project: Project instance
        role (str): 'leader' or 'provider'
    """
    from django.utils.dateformat import format as date_format
    
    role_display = 'Project Leader' if role == 'leader' else 'Project Provider'
    start_date = date_format(project.start_date, 'F d, Y')
    end_date = date_format(project.estimated_end_date, 'F d, Y')
    
    subject = f'You have been added to project: {project.title}'
    message = f'You have been added to the project "{project.title}" as {role_display}.\n\nProject Period: {start_date} - {end_date}'
    
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    🎉 Added to Project
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    You've been added to a project
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    You have been assigned to the following project as <strong>{role_display}</strong>:
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 20px; background-color: #f9fafb;">
                                            <h3 style="margin: 0 0 15px 0; color: #1f2937; font-size: 18px;">
                                                {project.title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📋 Type:</strong> {project.get_project_type_display()}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📅 Start Date:</strong> {start_date}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📅 End Date:</strong> {end_date}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📍 Location:</strong> {project.primary_location}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>👥 Beneficiary:</strong> {project.primary_beneficiary}
                                            </p>
                                            <p style="margin: 0; color: #4b5563; font-size: 14px;">
                                                <strong>🎯 Events:</strong> {project.estimated_events} planned event(s)
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #f0fdf4; border-left: 4px solid #10b981; color: #065f46; font-size: 14px; line-height: 1.5;">
                                    <strong>✓ Welcome to the Team!</strong><br>
                                    You can now access this project in your dashboard and collaborate with other team members.
                                </p>
                            </td>
                        </tr>
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
        recipient_list=[recipient_email],
        html_message=html_message
    )


def async_send_new_submission(recipient_emails, submission):
    """
    Send email when a project receives a new submission.
    
    Args:
        recipient_emails (list): List of project team member email addresses
        submission: Submission instance
    """
    from django.utils.dateformat import format as date_format
    
    deadline = date_format(submission.deadline, 'F d, Y \a\t g:i A')
    submitted_at = date_format(submission.submitted_at, 'F d, Y \a\t g:i A') if submission.submitted_at else 'Not yet submitted'
    submitted_by_name = submission.submitted_by.get_full_name() if submission.submitted_by else 'Unknown'
    
    subject = f'New submission for {submission.project.title}'
    message = f'A new submission has been made for the project "{submission.project.title}".\n\nForm: {submission.downloadable.name}\nSubmitted by: {submitted_by_name}\nDeadline: {deadline}'
    
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 30px 40px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                    📄 New Submission
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px;">
                                    Project submission update
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    A new submission has been made for your project:
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0; border: 2px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                                    <tr>
                                        <td style="padding: 20px; background-color: #f9fafb;">
                                            <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                                                <strong>Project</strong>
                                            </p>
                                            <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 18px;">
                                                {submission.project.title}
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📋 Form:</strong> {submission.downloadable.name}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>👤 Submitted by:</strong> {submitted_by_name}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📅 Deadline:</strong> {deadline}
                                            </p>
                                            <p style="margin: 0 0 10px 0; color: #4b5563; font-size: 14px;">
                                                <strong>📊 Status:</strong> {submission.get_status_display()}
                                            </p>
                                            {f'<p style="margin: 0; color: #4b5563; font-size: 14px;"><strong>✓ Submitted:</strong> {submitted_at}</p>' if submission.submitted_at else ''}
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 20px 0 0 0; padding: 15px; background-color: #dbeafe; border-left: 4px solid #3b82f6; color: #1e40af; font-size: 14px; line-height: 1.5;">
                                    <strong>ℹ️ Action Required</strong><br>
                                    Please review this submission in the system and take appropriate action if needed.
                                </p>
                            </td>
                        </tr>
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
        recipient_list=recipient_emails,
        html_message=html_message
    )
