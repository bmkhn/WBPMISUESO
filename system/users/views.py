from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from system.users.models import College
from system.users.decorators import role_required
from .forms import LoginForm, ClientRegistrationForm, FacultyRegistrationForm, ImplementerRegistrationForm

import random


def get_role_constants():
    ADMIN_ROLES = ["VP", "DIRECTOR", "UESO"]
    SUPERUSER_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    FACULTY_ROLE = ["FACULTY", "IMPLEMENTER"]
    COORDINATOR_ROLE = ["COORDINATOR"]
    return ADMIN_ROLES, SUPERUSER_ROLES, FACULTY_ROLE, COORDINATOR_ROLE

def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template


# Helper function to create user-related log entries
def create_user_log(user, action, target_user, details, is_notification=False):
    """
    Create a log entry for user-related actions.
    
    Args:
        user: The user performing the action (None for registration)
        action: 'CREATE', 'UPDATE', or 'DELETE'
        target_user: The user being affected
        details: String describing what changed
        is_notification: Whether to create notifications from this log
    """
    from system.logs.models import LogEntry
    from django.urls import reverse
    
    LogEntry.objects.create(
        user=user,
        action=action,
        model='User',
        object_id=target_user.id,
        object_repr=str(target_user),
        details=details,
        url=reverse('user_details', kwargs={'id': target_user.id}) if action != 'DELETE' else '',
        is_notification=is_notification
    )


####################################################################################################

# Login, Logout, Forgot Password, and Role-Based Redirection Views
def login_view(request):
    logout(request) # Remove this line if you want to keep users logged in when they revisit the login page
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, email=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user:
                # Generate 2FA code
                code = str(random.randint(100000, 999999))
                
                # Send 2FA code via email
                try:
                    send_mail(
                        'Your Login Verification Code',
                        f'Your verification code is: {code}\n\nThis code will expire in 10 minutes.',
                        'noreply@yourdomain.com',
                        [user.email],
                        fail_silently=False,
                    )
                    print(f"Login 2FA code sent to {user.email}: {code}")  # Debug
                except Exception as e:
                    print(f"Email sending failed: {str(e)}")  # Debug
                
                # Store in session (including the backend attribute from authenticate())
                request.session['login_2fa_code'] = code
                request.session['pending_login_user_id'] = user.id
                request.session['pending_login_backend'] = user.backend  # Preserve backend
                request.session['remember_me'] = request.POST.get('remember') == 'on'
                
                return JsonResponse({'success': True, 'code': code})  # For testing
        else:
            return JsonResponse({'success': False, 'error': 'Invalid email or password.'})
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


def verify_login_2fa_view(request):
    """Verify 2FA code for login"""
    if request.method == 'POST':
        code_entered = request.POST.get('code')
        code_sent = request.session.get('login_2fa_code')
        user_id = request.session.get('pending_login_user_id')
        backend = request.session.get('pending_login_backend')
        remember_me = request.session.get('remember_me', False)
        
        print(f"DEBUG - Code entered: {code_entered}, Code sent: {code_sent}, User ID: {user_id}, Remember: {remember_me}")  # Debug
        
        if code_entered == code_sent and user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                
                # Restore the backend attribute to the user object
                user.backend = backend
                
                # Clear session data BEFORE login to preserve them
                request.session.pop('login_2fa_code', None)
                request.session.pop('pending_login_user_id', None)
                request.session.pop('pending_login_backend', None)
                request.session.pop('remember_me', None)
                
                # Login the user (this regenerates the session)
                login(request, user)
                
                # Set session expiry AFTER login
                if remember_me:
                    request.session.set_expiry(1209600)  # 2 weeks in seconds
                    print("DEBUG - Session set to 2 weeks")  # Debug
                else:
                    request.session.set_expiry(0)  # Browser close
                    print("DEBUG - Session set to browser close")  # Debug
                
                # Make sure session is saved
                request.session.modified = True
                
                return JsonResponse({'success': True})
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found.'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid verification code.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def logout_view(request):
    logout(request)
    return redirect('login')


def session_test_view(request):
    """Test page to check session settings"""
    context = {
        'session_expiry': request.session.get_expiry_age(),
        'expires_at_browser_close': request.session.get_expire_at_browser_close(),
    }
    return render(request, 'users/session_test.html', context)


def forgot_password_view(request):
    """Handle forgot password flow"""
    logout(request)
    return render(request, 'users/forgot_password.html')


def send_password_reset_code_view(request):
    """Send password reset code via email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required.'})
        
        # Check if user exists
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No account found with this email.'})
        
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        
        # Send password reset code via email
        try:
            send_mail(
                'Password Reset Code',
                f'Your password reset code is: {code}\n\nThis code will expire in 10 minutes.',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            print(f"Password reset code sent to {email}: {code}")  # Debug
        except Exception as e:
            print(f"Email sending failed: {str(e)}")  # Debug
        
        # Store code and email in session
        request.session['password_reset_code'] = code
        request.session['password_reset_email'] = email
        
        return JsonResponse({'success': True, 'code': code})  # For testing
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def verify_reset_code_view(request):
    """Verify password reset code"""
    if request.method == 'POST':
        code_entered = request.POST.get('code')
        verify_only = request.POST.get('verify_only', 'false')
        code_sent = request.session.get('password_reset_code')
        
        if not code_entered:
            return JsonResponse({'success': False, 'error': 'Code is required.'})
        
        if code_entered == code_sent:
            # Mark code as verified in session
            request.session['code_verified'] = True
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid verification code.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def reset_password_view(request):
    """Reset password after code verification"""
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        email = request.session.get('password_reset_email')
        code_verified = request.session.get('code_verified', False)
        
        if not new_password:
            return JsonResponse({'success': False, 'error': 'New password is required.'})
        
        if not code_verified:
            return JsonResponse({'success': False, 'error': 'Please verify your code first.'})
        
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Log the password change
                create_user_log(
                    user=user,
                    action='UPDATE',
                    target_user=user,
                    details="Password reset via forgot password",
                    is_notification=False
                )
                
                # Clear session data
                request.session.pop('password_reset_code', None)
                request.session.pop('password_reset_email', None)
                request.session.pop('code_verified', None)
                
                return JsonResponse({'success': True})
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found.'})
        else:
            return JsonResponse({'success': False, 'error': 'Session expired. Please start over.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def role_redirect(request):
    role = getattr(request.user, 'role', None)

    if role in ["IMPLEMENTER", "CLIENT", "FACULTY"]:
        return redirect("home")
    elif role in ["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"]:
        return redirect("dashboard")
    else:
        return redirect("home")

def home(request):
    return render(request, 'base_public.html')  # extends base_public.html

def dashboard(request):
    return render(request, 'base_internal.html')  # extends base_internal.html

####################################################################################################

# Registration Views for Different User Types
def check_email_view(request):
    email = request.GET.get('email', '').strip()
    exists = False
    if email:
        User = get_user_model()
        exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

def register_view(request):
    """Unified registration role selector"""
    logout(request)
    # Clear any pending registration data
    for key in ['pending_user_id', '2fa_code', 'registration_role', 'registration_data']:
        request.session.pop(key, None)
    return render(request, 'users/register.html')


def send_verification_code_view(request):
    """Send verification code to email without creating user"""
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        if not email or not role:
            return JsonResponse({'success': False, 'error': 'Email and role are required.'})
        
        # Check if email already exists
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'This email is already registered.'})
        
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        
        # Send verification code via email
        try:
            send_mail(
                'Your Verification Code',
                f'Your verification code is: {code}\n\nThis code will expire in 10 minutes.',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            print(f"Verification code sent to {email}: {code}")  # Debug
        except Exception as e:
            print(f"Email sending failed: {str(e)}")  # Debug

        # Store code and email in session
        request.session['2fa_code'] = code
        request.session['pending_email'] = email
        request.session['registration_role'] = role
        
        # Return code in response for testing purposes
        return JsonResponse({'success': True, 'code': code})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def registration_unified_view(request, role):
    """Unified registration view for all roles (faculty, implementer, client)"""
    # Validate role
    role_upper = role.upper()
    valid_roles = ['FACULTY', 'IMPLEMENTER', 'CLIENT']
   
    if role_upper == 'THANK-YOU':
        return redirect('thank_you')
    elif role_upper not in valid_roles:
        return redirect('register')
    
    from .forms import UnifiedRegistrationForm
    error = None
    email = None
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        
        # Step 4: Verify code and create user
        if verification_code:
            code_sent = request.session.get('2fa_code')
            pending_email = request.session.get('pending_email')
            
            if verification_code != code_sent:
                return JsonResponse({'success': False, 'error': 'Invalid verification code.'})
            
            form = UnifiedRegistrationForm(request.POST, request.FILES, role=role_upper)
            
            if form.is_valid():
                user = form.save(commit=False)
                user.role = role_upper
                user.username = form.cleaned_data['email']
                user.is_confirmed = False  # User needs admin verification
                user.set_password(form.cleaned_data['password'])
                user.save()
                
                # Log the registration
                create_user_log(
                    user=None,  # Self-registration
                    action='CREATE',
                    target_user=user,
                    details=f"Self-registered as {user.get_role_display()}",
                    is_notification=False
                )
                
                # Clear session data
                request.session.pop('2fa_code', None)
                request.session.pop('pending_email', None)
                request.session.pop('registration_role', None)

                # Return JSON success (frontend will show Step 5)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid form data.'})
        else:
            # Normal POST without verification code - just show the form again
            form = UnifiedRegistrationForm(role=role_upper)
    else:
        form = UnifiedRegistrationForm(role=role_upper)
    
    # Get colleges for faculty
    colleges = College.objects.all() if role_upper == 'FACULTY' else None
    
    return render(request, 'users/registration_unified.html', {
        'form': form,
        'error': error,
        'email': email,
        'role': role_upper,
        'role_display': role.capitalize(),
        'colleges': colleges,
    })


def verify_unified_view(request):
    """Unified verification view for all roles"""
    error = None
    role = "THANK-YOU"
    
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        pending_user_id = request.session.get('pending_user_id')
        
        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.save()

                for key in ['2fa_code', 'pending_user_id', 'registration_role']:
                    request.session.pop(key, None)
                
                return redirect('thank_you')
            except User.DoesNotExist:
                error = "User not found. Please try registering again."
        else:
            error = "Invalid verification code. Please try again."
    
    return render(request, 'users/verify_unified.html', {
        'error': error,
        'role': role,
        'role_display': role.capitalize()
    })


def thank_you_view(request):
    """Legacy thank you page - no longer used, kept for backward compatibility"""
    return render(request, 'users/thank_you.html')

####################################################################################################

def not_authenticated_view(request):
    return render(request, 'users/403_not_authenticated.html', status=403)

def no_permission_view(request):
    return render(request, 'users/403_no_permission.html', status=403)

def not_confirmed_view(request):
    return render(request, 'users/403_not_confirmed.html', status=403)

####################################################################################################

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def manage_user(request):
    query_params = {}
    User = get_user_model()
    users = User.objects.all()

    search = request.GET.get('search', '').strip()
    if search:
        # Search by full name (given_name, middle_initial, last_name, suffix)
        from django.db.models import Q
        users = users.filter(
            Q(given_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(middle_initial__icontains=search) |
            Q(suffix__icontains=search) |
            Q(email__icontains=search)
        )
        query_params['search'] = search

    # Filters
    sort_by = request.GET.get('sort_by', 'date')
    order = request.GET.get('order', 'desc')
    role = request.GET.get('role', '')
    verified = request.GET.get('verified', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    college = request.GET.get('college', '')
    campus = request.GET.get('campus', '')

    if sort_by:
        query_params['sort_by'] = sort_by
    if order:
        query_params['order'] = order
    if role:
        users = users.filter(role=role)
        query_params['role'] = role
    if verified == 'true':
        users = users.filter(is_confirmed=True)
        query_params['verified'] = 'true'
    elif verified == 'false':
        users = users.filter(is_confirmed=False)
        query_params['verified'] = 'false'
    if date_from:
        users = users.filter(date_joined__date__gte=date_from)
        query_params['date_from'] = date_from
    if date_to:
        users = users.filter(date_joined__date__lte=date_to)
        query_params['date_to'] = date_to
    if college:
        users = users.filter(college_id=college)
        query_params['college'] = college
    if campus:
        users = users.filter(campus=campus)
        query_params['campus'] = campus

    # Sorting
    if sort_by == 'name':
        sort_field = ['last_name', 'given_name', 'middle_initial', 'suffix']
    else:
        sort_map = {
            'email': 'email',
            'date': 'date_joined',
            'role': 'role',
        }
        sort_field = [sort_map.get(sort_by, 'last_name')]
    if order == 'desc':
        sort_field = ['-' + f for f in sort_field]
    users = users.order_by(*sort_field)

    paginator = Paginator(users, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5:
        page_range = range(1, total + 1)
    elif current <= 3:
        page_range = range(1, 6)
    elif current >= total - 2:
        page_range = range(total - 4, total + 1)
    else:
        page_range = range(current - 2, current + 3)

    # Roles for dropdown
    roles = list(User.Role.choices)
    colleges = College.objects.all()
    campuses = list(User.Campus.choices)

    # Build querystring for pagination/filter links
    from urllib.parse import urlencode
    querystring = urlencode(query_params)

    return render(request, 'users/manage_user.html', {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'sort_by': sort_by,
        'order': order,
        'role': role,
        'verified': verified,
        'date_from': date_from,
        'date_to': date_to,
        'college': college,
        'campus': campus,
        'roles': roles,
        'colleges': colleges,
        'campuses': campuses,
        'search': search,
        'querystring': querystring,
    })


def user_details_view(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    return render(request, 'users/user_details.html', {'user': user})



@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def add_user(request):
    User = get_user_model()
    error = None
    roles = list(User.Role.choices)
    colleges = College.objects.all()
    campus_choices = User.Campus.choices

    success = False
    if request.method == 'POST':
        data = request.POST
        if User.objects.filter(email=data.get('email')).exists():
            error = "Email already exists."
        else:
            try:
                user = User.objects.create(
                    last_name=data.get('last_name'),
                    given_name=data.get('given_name'),
                    middle_initial=data.get('middle_initial'),
                    suffix=data.get('suffix'),
                    sex=data.get('sex'),
                    email=data.get('email'),
                    contact_no=data.get('contact_no'),

                    role=data.get('role'),
                    username=data.get('email'),

                    college=College.objects.get(id=data.get('college')) if data.get('college') else None,
                    campus=data.get('campus') if data.get('campus') else None,
                    degree=data.get('degree'),
                    expertise=data.get('expertise'),
                    company=data.get('company'),
                    industry=data.get('industry'),

                    is_confirmed=True,
                    created_by=request.user,
                )
                user.set_password(data.get('password', ''))
                user.save()
                
                # Log the user creation
                create_user_log(
                    user=request.user,
                    action='CREATE',
                    target_user=user,
                    details=f"Created by {request.user.get_role_display()} - {user.get_role_display()}",
                    is_notification=True
                )

                success = True
            except Exception as e:
                error = str(e)
    return render(request, 'users/add_user.html', {
        'error': error,
        'success': success,
        'roles': roles,
        'colleges': colleges,
        'campus_choices': campus_choices,
    })

# Edit user view
@login_required
def edit_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    
    # Permission check: Users can edit themselves, or VP/DIRECTOR can edit anyone
    can_edit_role_and_verify = request.user.role in ["VP", "DIRECTOR"]
    can_edit_this_user = (request.user.id == user.id) or can_edit_role_and_verify
    
    if not can_edit_this_user:
        return redirect('no_permission')
    
    error = None
    roles = list(User.Role.choices)
    colleges = College.objects.all()
    campus_choices = User.Campus.choices

    success = False
    email_changed = False
    if request.method == 'POST':
        data = request.POST
        if User.objects.filter(email=data.get('email')).exclude(id=user.id).exists():
            error = "Email already exists."
        else:
            try:
                # Track what changed for logging
                changes = []
                old_role = user.role
                
                # All users can edit these fields
                user.last_name = data.get('last_name')
                user.given_name = data.get('given_name')
                user.middle_initial = data.get('middle_initial') or None
                user.suffix = data.get('suffix') or None
                user.sex = data.get('sex')
                user.contact_no = data.get('contact_no')
                
                # Email change requires verification (handled by frontend modal)
                new_email = data.get('email')
                if user.email != new_email:
                    changes.append('email')
                    email_changed = True
                    user.email = new_email
                    user.username = new_email

                # Only VP/DIRECTOR can change role
                if can_edit_role_and_verify:
                    new_role = data.get('role')
                    if user.role != new_role:
                        changes.append(f'role from {user.get_role_display()} to {dict(User.Role.choices)[new_role]}')
                    user.role = new_role

                # Role-specific field updates
                if user.role == "CLIENT":
                    user.college = None
                    user.campus = None
                    user.degree = None
                    user.expertise = None
                    # CLIENT can edit company and industry
                    user.company = data.get('company') or None
                    user.industry = data.get('industry') or None

                elif user.role == "FACULTY":
                    # FACULTY can edit campus, college, degree, and expertise
                    college_id = data.get('college')
                    user.college = College.objects.get(id=college_id) if college_id else None
                    user.campus = data.get('campus') or None
                    user.degree = data.get('degree') or None
                    user.expertise = data.get('expertise') or None
                    user.company = None
                    user.industry = None

                elif user.role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
                    # Only VP/DIRECTOR can edit these roles' info
                    if can_edit_role_and_verify:
                        college_id = data.get('college')
                        user.college = College.objects.get(id=college_id) if college_id else None
                        user.campus = data.get('campus') or None
                    user.degree = None
                    user.expertise = None
                    user.company = None
                    user.industry = None

                elif user.role == "IMPLEMENTER":
                    # IMPLEMENTER can edit degree and expertise
                    user.college = None
                    user.campus = None
                    user.degree = data.get('degree') or None
                    user.expertise = data.get('expertise') or None
                    user.company = None
                    user.industry = None
                
                else:
                    # UESO, DIRECTOR, VP - only editable by VP/DIRECTOR
                    if can_edit_role_and_verify:
                        user.college = None
                        user.campus = None
                        user.degree = None
                        user.expertise = None
                        user.company = None
                        user.industry = None

                # Only update password if provided and not blank
                password = data.get('password', '').strip()
                password_changed = False
                if password:
                    user.set_password(password)
                    password_changed = True
                    changes.append('password')

                user.save()
                
                # Log the user edit
                details = f"Edited by {request.user.get_role_display()}"
                if changes:
                    details += f" - Changed: {', '.join(changes)}"
                
                create_user_log(
                    user=request.user,
                    action='UPDATE',
                    target_user=user,
                    details=details,
                    is_notification=True
                )
                
                success = True
            except Exception as e:
                error = str(e)
    
    return render(request, 'users/edit_user.html', {
        'user': user,
        'error': error,
        'success': success,
        'email_changed': email_changed,
        'colleges': colleges,
        'campus_choices': campus_choices,
        'roles': roles,
        'can_edit_role_and_verify': can_edit_role_and_verify,
        'is_editing_self': request.user.id == user.id,
    })


# Verify/Unverify user views
from django.http import HttpResponseRedirect

@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def verify_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    
    # VP/DIRECTOR cannot verify themselves
    if request.user.id == user.id:
        return redirect('no_permission')
    
    user.is_confirmed = True
    user.save()
    from urllib.parse import quote
    return redirect(f'/users/?success=true&action=confirmed&title={quote(user.get_full_name())}')

@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def unverify_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    
    # VP/DIRECTOR cannot unverify themselves
    if request.user.id == user.id:
        return redirect('no_permission')
    
    user.is_confirmed = False
    user.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


from django.http import HttpResponseRedirect
from django.urls import reverse

# Delete user view with confirmation
@role_required(allowed_roles=["VP", "DIRECTOR"], require_confirmed=True)
def delete_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    user.delete()
    return HttpResponseRedirect(reverse('manage_user'))

####################################################################################################

# User Profile View
from django.contrib.auth.decorators import login_required
from django.db.models import Q


def profile_role_constants():
    HAS_COLLEGE_CAMPUS = ["FACULTY", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    HAS_DEGREE_EXPERTISE = ["FACULTY", "IMPLEMENTER"]
    HAS_COMPANY_INDUSTRY = ["CLIENT"]
    return HAS_COLLEGE_CAMPUS, HAS_DEGREE_EXPERTISE, HAS_COMPANY_INDUSTRY


def can_view_project(user, project):
    """
    Check if a user can view a project based on visibility restrictions:
    - Non-authenticated users: only COMPLETED projects
    - Project leader/providers: can see their projects regardless of status
    - Dean/Coordinator/Program Head: can see all projects from their college
    - UESO/Director/VP: can see everything
    """
    # UESO, Director, VP can see everything
    if user.is_authenticated and hasattr(user, 'role'):
        if user.role in ["UESO", "DIRECTOR", "VP"]:
            return True
        
        # Project leader or provider can see their own projects
        if project.project_leader == user or user in project.providers.all():
            return True
        
        # Dean, Coordinator, Program Head can see all projects from their college
        if user.role in ["DEAN", "COORDINATOR", "PROGRAM_HEAD"]:
            if user.college and project.project_leader.college == user.college:
                return True
    
    # Non-authenticated or other users can only see COMPLETED projects
    return project.status == 'COMPLETED'


def profile_view(request, id=None):
    # If id is provided, show that user's profile, otherwise show logged-in user's profile
    User = get_user_model()
    if id:
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return redirect('profile')  # Fallback to own profile if user not found
    else:
        user = request.user
    
    HAS_COLLEGE_CAMPUS, HAS_DEGREE_EXPERTISE, HAS_COMPANY_INDUSTRY = profile_role_constants()

    base_template = get_templates(request)

    # Get campus display name
    campus_display = dict(User.Campus.choices).get(user.campus, user.campus) if user.campus else "N/A"

    # Get college name and logo
    college_name = user.college.name if user.college else "N/A"
    college_logo = user.college.logo.url if user.college and user.college.logo else None

    # Get content items based on role
    # For ALL roles except CLIENT: show only projects where the profile user is leader or provider
    # Then apply visibility filtering based on what the VIEWING user can see
    content_items = []

    if user.role == User.Role.CLIENT:
        # Get client requests
        from shared.request.models import ClientRequest
        content_items = ClientRequest.objects.filter(
            submitted_by=user
        ).order_by('-submitted_at')
    
    else:
        # For all other roles: Get only THEIR OWN projects (where they are leader or provider)
        from shared.projects.models import Project
        all_projects = Project.objects.filter(
            Q(project_leader=user) | Q(providers=user)
        ).distinct().select_related(
            'project_leader', 'agenda'
        ).prefetch_related(
            'providers', 'sdgs'
        ).order_by('-start_date')
        
        # Filter projects based on what the VIEWING user can see
        content_items = [p for p in all_projects if can_view_project(request.user, p)]

    return render(request, 'users/profile.html', {
        'profile_user': user,  # The user whose profile is being viewed
        'can_edit': request.user.id == user.id,  # Can only edit own profile
        'campus_display': campus_display,
        'college_name': college_name,
        'college_logo': college_logo,
        'content_items': content_items,
        'content_items_count': len(content_items),  # Count of visible items
        'base_template': base_template,

        'HAS_COLLEGE_CAMPUS': HAS_COLLEGE_CAMPUS,
        'HAS_DEGREE_EXPERTISE': HAS_DEGREE_EXPERTISE,
        'HAS_COMPANY_INDUSTRY': HAS_COMPANY_INDUSTRY,
    })


@login_required
def update_bio(request):
    if request.method == 'POST':
        bio = request.POST.get('bio', '').strip()
        user = request.user
        user.bio = bio
        user.save(update_fields=['bio'])
        
    return redirect('profile')


@login_required
def update_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        user = request.user
        user.profile_picture = request.FILES['profile_picture']
        user.save(update_fields=['profile_picture'])
        
    return redirect('profile')

####################################################################################################

# Quick Login View for Testing Purposes
User = get_user_model()

def quick_login(request, role):
    from django.contrib.auth import login
    from django.contrib.auth import authenticate

    username = f"{role.lower()}@example.com"
    password = "test1234"

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return redirect("role_redirect")
    else:
        return redirect("login") 

## temp stuff
def newp_view(request):
    logout(request)
    return render(request, 'users/new_pass.html')

def otp_view(request):
    logout(request)
    return render(request, 'users/otp.html')

def end(request):
    logout(request)