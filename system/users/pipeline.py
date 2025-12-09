"""
Social Auth Pipeline for Google Sign-In integration.

This pipeline handles user creation and authentication when users sign in with Google.
It extracts user data from Google and creates a User account if one doesn't exist,
or logs in the existing user if the email matches.
"""

from django.contrib.auth import get_user_model
from .views import _is_psu_email, create_user_log
from social_core.pipeline.user import get_username as social_get_username
from social_core.exceptions import AuthException

User = get_user_model()


def get_username(strategy, details, backend, user=None, *args, **kwargs):
    """
    Generate a username from the email address.
    This is required because our User model uses email as USERNAME_FIELD,
    but social-auth still needs a username field.
    """
    if user:
        return {'username': user.username}
    
    email = details.get('email')
    if not email:
        raise AuthException(backend, 'Email is required for authentication.')
    
    return {'username': email}


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Create a new user if one doesn't exist with the given email.
    This function is called when is_new=True in the pipeline.
    If user already exists (from social_user step), we skip creation.
    """
    if user:
        return {'is_new': False}
    
    email = details.get('email')
    if not email:
        raise AuthException(backend, 'Email is required for authentication.')
    
    # Double-check if user exists (safety check)
    try:
        existing_user = User.objects.get(email=email)
        return {
            'is_new': False,
            'user': existing_user
        }
    except User.DoesNotExist:
        pass
    
    # Extract name information from Google
    full_name = details.get('fullname', '')
    first_name = details.get('first_name', '')
    last_name = details.get('last_name', '')
    
    # Parse full name if first/last not provided
    if not first_name and not last_name and full_name:
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Set defaults for required fields that Google doesn't provide
    # Users must complete these via profile completion
    given_name = first_name or ''
    last_name = last_name or ''
    sex = 'MALE'  # Default, user can update later
    contact_no = ''  # Empty, user must add
    
    # Determine role based on email domain
    # If @psu.palawan.edu.ph → automatically assign FACULTY and mark selection done
    # Otherwise → needs role selection (set CLIENT temporarily)
    if _is_psu_email(email):
        role = User.Role.FACULTY
        google_role_selected = True
    else:
        role = User.Role.CLIENT
        google_role_selected = False
    
    # Create the user with minimal required fields
    # Use a temporary password, then set it to unusable
    import secrets
    temp_password = secrets.token_urlsafe(32)
    user = User.objects.create_user(
        username=email,  # Use email as username
        email=email,
        given_name=given_name or 'Google',  # Temporary placeholder
        last_name=last_name or 'User',  # Temporary placeholder
        sex=sex,
        contact_no=contact_no,
        role=role,
        google_role_selected=google_role_selected,
        is_confirmed=True,  # Google-verified emails are considered confirmed
        password=temp_password,  # Temporary password, will be set to unusable
    )
    
    # Set unusable password for security (users can't login with password)
    user.set_unusable_password()
    
    # Mark user as needing profile completion
    # We'll use a session flag or check profile completeness in redirect
    user.save()
    
    # Log the user creation
    create_user_log(
        user=None,
        action='CREATE',
        target_user=user,
        details=f"Registered via Google Sign-In",
        is_notification=False
    )
    
    return {
        'is_new': True,
        'user': user
    }


def user_details(strategy, details, backend, user=None, *args, **kwargs):
    """
    Update user details from Google profile information.
    This is called for both new and existing users.
    """
    if not user:
        return
    
    changed = False
    
    # Update name if provided and different (only if still placeholder)
    if details.get('first_name') and user.given_name in ['Google', '']:
        user.given_name = details.get('first_name')
        changed = True
    
    if details.get('last_name') and user.last_name in ['User', '']:
        user.last_name = details.get('last_name')
        changed = True
    
    # Update profile picture if available and not set
    if details.get('picture') and not user.profile_picture:
        # Note: You might want to download and save the image
        # For now, we'll skip this as it requires additional handling
        pass
    
    if changed:
        user.save()
    
    # Store flags in session for new Google users
    is_new = kwargs.get('is_new', False)
    if is_new:
        strategy.session_set('google_profile_incomplete', True)
        # Only non-PSU emails need role selection (PSU emails are auto-assigned FACULTY)
        email = details.get('email', '')
        if not email.lower().endswith('@psu.palawan.edu.ph'):
            strategy.session_set('google_role_selection_needed', True)
    
    return {
        'user': user
    }

