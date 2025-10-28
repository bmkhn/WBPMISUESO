from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from urllib.parse import urlencode

from system.users.models import College, User
from system.users.decorators import role_required
from .forms import LoginForm, ClientRegistrationForm, FacultyRegistrationForm, ImplementerRegistrationForm
from shared.projects.models import Project
from shared.request.models import ClientRequest

import random
import logging

logger = logging.getLogger(__name__)


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

def profile_role_constants():
    HAS_COLLEGE_CAMPUS = ["FACULTY", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "IMPLEMENTER"]
    HAS_DEGREE_EXPERTISE = ["FACULTY", "IMPLEMENTER"]
    HAS_COMPANY_INDUSTRY = ["CLIENT"]
    return HAS_COLLEGE_CAMPUS, HAS_DEGREE_EXPERTISE, HAS_COMPANY_INDUSTRY


def login_view(request):
    logout(request)
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(request, email=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user:
                login(request, user)
                return redirect('role_redirect')
            else:
                messages.error(request, "Invalid email or password.")
                
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def forgot_password_view(request):
    logout(request)
    if request.method == 'POST':
        email = request.POST.get('email')
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is: {otp}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, 'An OTP has been sent to your email.')
            return redirect('otp') 
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email address.')
        except Exception as e:
            logger.error(f"Error sending password reset email to {email}: {e}")
            messages.error(request, 'Failed to send OTP. Please try again.')
            
    return render(request, 'users/forgot_password.html')

def otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired or invalid request.')
        return redirect('forgot_password')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('reset_otp')

        if entered_otp == stored_otp:
            request.session['otp_verified'] = True
            messages.success(request, 'OTP verified successfully.')
            return redirect('new_password') 
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            
    return render(request, 'users/otp.html', {'email': email})

def newp_view(request):
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified')

    if not email or not otp_verified:
        messages.error(request, 'Please verify OTP first.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and new_password == confirm_password:
            if len(new_password) < 8: # Basic validation
                 messages.error(request, 'Password must be at least 8 characters long.')
            else:
                User = get_user_model()
                try:
                    user = User.objects.get(email=email)
                    user.set_password(new_password)
                    user.save()
                    
                    request.session.pop('reset_email', None)
                    request.session.pop('reset_otp', None)
                    request.session.pop('otp_verified', None)
                    
                    messages.success(request, 'Password has been reset successfully.')
                    return redirect('end_change_password') 
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')
                except Exception as e:
                    logger.error(f"Error resetting password for {email}: {e}")
                    messages.error(request, 'An error occurred while resetting the password.')
        else:
            messages.error(request, 'Passwords do not match.')
            
    return render(request, 'users/new_pass.html')
    
def end(request):
    return render(request, 'users/end_changepass.html')


def role_redirect(request):
    role = getattr(request.user, 'role', None)
    if role in ["IMPLEMENTER", "CLIENT", "FACULTY"]:
        return redirect("home")
    elif role in ["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"]:
        return redirect("dashboard")
    else:
        return redirect("home")

def home(request):
    base_template = get_templates(request)
    return render(request, 'external/home/templates/home/home.html', {'base_template': base_template})

def dashboard(request):
    base_template = get_templates(request)
    # Add dashboard-specific context here if needed
    return render(request, 'internal/dashboard/templates/dashboard/dashboard.html', {'base_template': base_template})


def check_email_view(request):
    email = request.GET.get('email', '').strip()
    exists = False
    if email:
        User = get_user_model()
        exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

def register_view(request):
    logout(request)
    return render(request, 'users/register.html')

def registration_client_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            try:
                send_mail(
                    'Your 2FA Verification Code',
                    f'Your verification code is: {code}',
                    'noreply@yourdomain.com',
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                 logger.error(f"Failed to send verification email to {email}: {e}")
                 messages.error(request, "Could not send verification email. Please try again later.")
                 return render(request, 'users/registration_client.html', {'form': form})
            
            user = form.save(commit=False)
            user.is_confirmed = False
            user.username = user.email
            user.role = User.Role.CLIENT
            user.set_password(form.cleaned_data['password'])
            user.save()

            request.session['pending_user_id'] = user.id
            request.session['2fa_code'] = code
            return redirect('verify_client')
        else:
            error = "Please correct the errors below."
            return render(request, 'users/registration_client.html', {'form': form, 'error': error})
    else:
        form = ClientRegistrationForm()
        return render(request, 'users/registration_client.html', {'form': form})

def client_verify_view(request):
    error = None
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        pending_user_id = request.session.get('pending_user_id')

        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.is_confirmed = True # Confirm the user
                user.save(update_fields=['is_confirmed'])
            except User.DoesNotExist:
                error = "User not found. Please register again."
                return render(request, 'users/verify_client.html', {'error': error})
            
            request.session.pop('pending_user_id', None)
            request.session.pop('2fa_code', None)
            messages.success(request, "Account verified successfully!")
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
            if not pending_user_id:
                 error = "Session expired. Please register again."
    return render(request, 'users/verify_client.html', {'error': error})


def registration_faculty_view(request):
    error = None
    email = None
    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            try:
                send_mail('Your 2FA Verification Code', f'Your verification code is: {code}', 'noreply@yourdomain.com', [email], fail_silently=False)
            except Exception as e:
                 logger.error(f"Failed to send verification email to {email}: {e}")
                 messages.error(request, "Could not send verification email. Please try again later.")
                 return render(request, 'users/registration_faculty.html', {'form': form})

            user = form.save(commit=False)
            user.is_confirmed = False
            user.username = user.email
            user.role = User.Role.FACULTY
            user.set_password(form.cleaned_data['password'])
            user.save()
            request.session['pending_user_id'] = user.id
            request.session['2fa_code'] = code
            return redirect('verify_faculty')
        else:
             error = "Please correct the errors below."
             return render(request, 'users/registration_faculty.html', {'form': form, 'error': error})
    else:
        form = FacultyRegistrationForm()
    return render(request, 'users/registration_faculty.html', {'form': form})

def faculty_verify_view(request):
    error = None
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        pending_user_id = request.session.get('pending_user_id')
        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.is_confirmed = True
                user.save(update_fields=['is_confirmed'])
            except User.DoesNotExist:
                error = "User not found. Please register again."
                return render(request, 'users/verify_faculty.html', {'error': error})
            request.session.pop('pending_user_id', None)
            request.session.pop('2fa_code', None)
            messages.success(request, "Account verified successfully!")
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
            if not pending_user_id:
                 error = "Session expired. Please register again."
    return render(request, 'users/verify_faculty.html', {'error': error})


def registration_implementer_view(request):
    error = None
    email = None
    if request.method == 'POST':
        form = ImplementerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            try:
                send_mail('Your 2FA Verification Code', f'Your verification code is: {code}', 'noreply@yourdomain.com', [email], fail_silently=False)
            except Exception as e:
                 logger.error(f"Failed to send verification email to {email}: {e}")
                 messages.error(request, "Could not send verification email. Please try again later.")
                 return render(request, 'users/registration_implementer.html', {'form': form})

            user = form.save(commit=False)
            user.is_confirmed = False
            user.username = user.email
            user.role = User.Role.IMPLEMENTER
            user.set_password(form.cleaned_data['password'])
            user.save()
            request.session['pending_user_id'] = user.id
            request.session['2fa_code'] = code
            return redirect('verify_implementer')
        else:
             error = "Please correct the errors below."
             return render(request, 'users/registration_implementer.html', {'form': form, 'error': error})
    else:
        form = ImplementerRegistrationForm()
    return render(request, 'users/registration_implementer.html', {'form': form})


def implementer_verify_view(request):
    error = None
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        pending_user_id = request.session.get('pending_user_id')
        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.is_confirmed = True
                user.save(update_fields=['is_confirmed'])
            except User.DoesNotExist:
                error = "User not found. Please register again."
                return render(request, 'users/verify_implementer.html', {'error': error})
            request.session.pop('pending_user_id', None)
            request.session.pop('2fa_code', None)
            messages.success(request, "Account verified successfully!")
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
            if not pending_user_id:
                 error = "Session expired. Please register again."
    return render(request, 'users/verify_implementer.html', {'error': error})


def thank_you_view(request):    
    return render(request, 'users/thank_you.html')


def not_authenticated_view(request):
    return render(request, 'users/403_not_authenticated.html', status=403)

def no_permission_view(request):
    return render(request, 'users/403_no_permission.html', status=403)

def not_confirmed_view(request):
    return render(request, 'users/403_not_confirmed.html', status=403)


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def manage_user(request):
    query_params = {}
    User = get_user_model()
    users_qs = User.objects.select_related('college').all()

    search = request.GET.get('search', '').strip()
    if search:
        users_qs = users_qs.filter(
            Q(given_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(middle_initial__icontains=search) |
            Q(suffix__icontains=search) |
            Q(email__icontains=search)
        )
        query_params['search'] = search

    sort_by = request.GET.get('sort_by', 'date')
    order = request.GET.get('order', 'desc')
    role = request.GET.get('role', '')
    verified = request.GET.get('verified', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    college_id = request.GET.get('college', '')
    campus = request.GET.get('campus', '')

    query_params['sort_by'] = sort_by
    query_params['order'] = order
    if role:
        users_qs = users_qs.filter(role=role)
        query_params['role'] = role
    if verified == 'true':
        users_qs = users_qs.filter(is_confirmed=True)
        query_params['verified'] = 'true'
    elif verified == 'false':
        users_qs = users_qs.filter(is_confirmed=False)
        query_params['verified'] = 'false'
    if date_from:
        users_qs = users_qs.filter(date_joined__date__gte=date_from)
        query_params['date_from'] = date_from
    if date_to:
        users_qs = users_qs.filter(date_joined__date__lte=date_to)
        query_params['date_to'] = date_to
    if college_id:
        users_qs = users_qs.filter(college_id=college_id)
        query_params['college'] = college_id
    if campus:
        users_qs = users_qs.filter(campus=campus)
        query_params['campus'] = campus

    if sort_by == 'name':
        sort_field = ['last_name', 'given_name']
    else:
        sort_map = {'email': 'email', 'date': 'date_joined', 'role': 'role'}
        sort_field = [sort_map.get(sort_by, 'date_joined')]
        
    order_prefix = '-' if order == 'desc' else ''
    sort_field_ordered = [order_prefix + f for f in sort_field]
    users_qs = users_qs.order_by(*sort_field_ordered)

    paginator = Paginator(users_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    current = page_obj.number
    total = paginator.num_pages
    if total <= 5: page_range = range(1, total + 1)
    elif current <= 3: page_range = range(1, 6)
    elif current >= total - 2: page_range = range(total - 4, total + 1)
    else: page_range = range(current - 2, current + 3)

    roles = list(User.Role.choices)
    colleges = College.objects.all()
    campuses = list(User.Campus.choices)

    querystring = urlencode({k: v for k, v in query_params.items() if v})

    context = {
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
        'college': college_id,
        'campus': campus,
        'roles': roles,
        'colleges': colleges,
        'campuses': campuses,
        'search': search,
        'querystring': querystring,
        'base_template': get_templates(request)
    }
    return render(request, 'users/manage_user.html', context)


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def user_details_view(request, id):
    User = get_user_model()
    user = get_object_or_404(User.objects.select_related('college'), id=id)
    return render(request, 'users/user_details.html', {'user': user, 'base_template': get_templates(request)})



@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def add_user(request):
    User = get_user_model()
    error = None
    roles = list(User.Role.choices)
    colleges = College.objects.all()
    campus_choices = User.Campus.choices
    success = False

    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        
        if not email:
            error = "Email is required."
        elif User.objects.filter(email=email).exists():
            error = "Email already exists."
        else:
            try:
                college = None
                if data.get('college'):
                    college = College.objects.get(id=data.get('college'))
                
                user = User(
                    last_name=data.get('last_name'),
                    given_name=data.get('given_name'),
                    middle_initial=data.get('middle_initial') or None,
                    suffix=data.get('suffix') or None,
                    sex=data.get('sex'),
                    email=email,
                    contact_no=data.get('contact_no') or None,
                    role=data.get('role'),
                    username=email, 
                    college=college,
                    campus=data.get('campus') or None,
                    degree=data.get('degree') or None,
                    expertise=data.get('expertise') or None,
                    company=data.get('company') or None,
                    industry=data.get('industry') or None,
                    is_confirmed=True,
                )
                password = data.get('password', '').strip()
                if password:
                    user.set_password(password)
                else:
                    error = "Password is required for new users."
                
                if not error:
                     user.full_clean() # Validate model fields
                     user.save()
                     messages.success(request, f"User '{user.get_full_name()}' added successfully.")
                     success = True
                     # Optionally redirect after success: return redirect('manage_user')
            except College.DoesNotExist:
                 error = "Selected college does not exist."
            except Exception as e:
                 logger.error(f"Error adding user {email}: {e}")
                 error = f"An error occurred: {e}"
                 
    context = {
        'error': error,
        'success': success,
        'roles': roles,
        'colleges': colleges,
        'campus_choices': campus_choices,
        'base_template': get_templates(request)
    }
    return render(request, 'users/add_user.html', context)


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def edit_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    error = None
    roles = list(User.Role.choices)
    colleges = College.objects.all()
    campus_choices = User.Campus.choices
    success = False

    if request.method == 'POST':
        data = request.POST
        new_email = data.get('email')

        if not new_email:
             error = "Email cannot be empty."
        elif User.objects.filter(email=new_email).exclude(id=user.id).exists():
            error = "Email already exists for another user."
        else:
            try:
                user.last_name = data.get('last_name')
                user.given_name = data.get('given_name')
                user.middle_initial = data.get('middle_initial') or None
                user.suffix = data.get('suffix') or None
                user.sex = data.get('sex')
                user.email = new_email
                user.username = new_email # Keep username synced
                user.contact_no = data.get('contact_no') or None
                user.role = data.get('role')

                college_id = data.get('college')
                user.college = College.objects.get(id=college_id) if college_id else None
                user.campus = data.get('campus') or None
                user.degree = data.get('degree') or None
                user.expertise = data.get('expertise') or None
                user.company = data.get('company') or None
                user.industry = data.get('industry') or None

                password = data.get('password', '').strip()
                if password:
                    user.set_password(password)

                user.full_clean()
                user.save()
                messages.success(request, f"User '{user.get_full_name()}' updated successfully.")
                success = True
                # Optionally redirect after success: return redirect('manage_user')
            except College.DoesNotExist:
                 error = "Selected college does not exist."
            except Exception as e:
                logger.error(f"Error editing user {id}: {e}")
                error = f"An error occurred: {e}"
                
    context = {
        'user': user,
        'error': error,
        'success': success,
        'colleges': colleges,
        'campus_choices': campus_choices,
        'roles': roles,
        'base_template': get_templates(request)
    }
    return render(request, 'users/edit_user.html', context)


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def verify_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    if not user.is_confirmed:
        user.is_confirmed = True
        user.save(update_fields=['is_confirmed'])
        messages.success(request, f"User '{user.get_full_name()}' has been verified.")
    else:
        messages.info(request, f"User '{user.get_full_name()}' is already verified.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('manage_user')))

@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def unverify_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    if user.is_confirmed:
        user.is_confirmed = False
        user.save(update_fields=['is_confirmed'])
        messages.success(request, f"User '{user.get_full_name()}' has been unverified.")
    else:
        messages.info(request, f"User '{user.get_full_name()}' is already unverified.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('manage_user')))


@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"], require_confirmed=True)
def delete_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    
    # Prevent deleting oneself or superusers if needed (add logic here)
    if request.user.id == user.id:
        messages.error(request, "You cannot delete your own account.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('manage_user')))

    if request.method == 'POST':
        try:
            user_name = user.get_full_name()
            user.delete()
            messages.success(request, f"User '{user_name}' deleted successfully.")
            return redirect('manage_user')
        except Exception as e:
            logger.error(f"Error deleting user {id}: {e}")
            messages.error(request, f"An error occurred while deleting the user: {e}")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('manage_user')))
            
    # If GET, show confirmation page (create confirm_delete_user.html template)
    return render(request, 'users/confirm_delete_user.html', {'user_to_delete': user, 'base_template': get_templates(request)})


@login_required
def profile_view(request, id=None):
    User = get_user_model()
    profile_user = None
    can_edit = False

    if id and str(request.user.id) != str(id): 
        try:
            profile_user = User.objects.select_related('college').get(id=id)
            can_edit = False 
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('profile') 
    else:
        profile_user = User.objects.select_related('college').get(id=request.user.id)
        can_edit = True 

    HAS_COLLEGE_CAMPUS, HAS_DEGREE_EXPERTISE, HAS_COMPANY_INDUSTRY = profile_role_constants()
    base_template = get_templates(request)
    
    campus_display = dict(User.Campus.choices).get(profile_user.campus, profile_user.campus) if profile_user.campus else "N/A"
    college_name = profile_user.college.name if profile_user.college else "N/A"
    college_logo = profile_user.college.logo.url if profile_user.college and hasattr(profile_user.college, 'logo') and profile_user.college.logo else None
    
    content_items = []
    if profile_user.role in [User.Role.FACULTY, User.Role.IMPLEMENTER]:
        content_items = Project.objects.filter(Q(project_leader=profile_user) | Q(providers=profile_user)).distinct().select_related('project_leader', 'agenda').prefetch_related('providers').order_by('-start_date')
    elif profile_user.role in [User.Role.PROGRAM_HEAD, User.Role.DEAN, User.Role.COORDINATOR]:
        if profile_user.college:
            content_items = Project.objects.filter(project_leader__college=profile_user.college).distinct().select_related('project_leader', 'agenda').prefetch_related('providers').order_by('-start_date')
        else:
             content_items = Project.objects.none()
    elif profile_user.role == User.Role.CLIENT:
        content_items = ClientRequest.objects.filter(submitted_by=profile_user).order_by('-submitted_at')
        
    context = {
        'profile_user': profile_user,
        'can_edit': can_edit,
        'campus_display': campus_display,
        'college_name': college_name,
        'college_logo': college_logo,
        'content_items': content_items,
        'base_template': base_template,
        'HAS_COLLEGE_CAMPUS': HAS_COLLEGE_CAMPUS,
        'HAS_DEGREE_EXPERTISE': HAS_DEGREE_EXPERTISE,
        'HAS_COMPANY_INDUSTRY': HAS_COMPANY_INDUSTRY,
        'campus_choices': User.Campus.choices if can_edit else None, 
    }
    return render(request, 'users/profile.html', context) 


@login_required
def update_profile_view(request):
    if request.method == 'POST':
        user = request.user 
        try:
            update_fields = [] 

            def check_and_update(field_name, post_key=None, is_file=False, allow_empty=True):
                 nonlocal user, update_fields, request
                 key = post_key or field_name
                 current_value = getattr(user, field_name, None)
                 
                 if is_file:
                     if key in request.FILES:
                         setattr(user, field_name, request.FILES[key])
                         if field_name not in update_fields: update_fields.append(field_name)
                 else:
                     new_value = request.POST.get(key)
                     if not allow_empty and new_value == '':
                         new_value = None
                     if field_name == 'campus' and new_value == '': 
                          new_value = None
                     if str(current_value or '') != str(new_value or ''): 
                         setattr(user, field_name, new_value)
                         if field_name not in update_fields: update_fields.append(field_name)

            check_and_update('given_name')
            check_and_update('last_name')
            check_and_update('contact_no', allow_empty=False) 
            check_and_update('bio', allow_empty=False) 

            new_email = request.POST.get('email')
            if user.email != new_email:
                if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                     messages.error(request, f"Email '{new_email}' is already in use by another account.")
                     return redirect('profile') 
                user.email = new_email
                user.username = new_email 
                if 'email' not in update_fields: update_fields.append('email')
                if 'username' not in update_fields: update_fields.append('username')

            HAS_COLLEGE_CAMPUS, HAS_DEGREE_EXPERTISE, HAS_COMPANY_INDUSTRY = profile_role_constants()
            
            if user.role in HAS_COLLEGE_CAMPUS:
                 check_and_update('campus', allow_empty=False) 

            if user.role in HAS_DEGREE_EXPERTISE:
                 check_and_update('expertise', allow_empty=False)
                 check_and_update('degree', allow_empty=False)

            if user.role in HAS_COMPANY_INDUSTRY:
                 check_and_update('company', allow_empty=False)
                 check_and_update('industry', allow_empty=False)

            check_and_update('profile_picture', is_file=True)

            if update_fields:
                user.full_clean() # Run model validation
                user.save(update_fields=update_fields)
                messages.success(request, 'Profile updated successfully!')
            else:
                 messages.info(request, 'No changes were made.')

        except Exception as e:
             logger.error(f"Error updating profile for user {user.id}: {e}") 
             messages.error(request, f"An error occurred while updating your profile: {e}")

        return redirect('profile') 

    else:
        return redirect('profile')


User = get_user_model()

def quick_login(request, role):
    username = f"{role.lower()}@example.com"
    password = "test1234" 
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return redirect("role_redirect")
    else:
        messages.error(request, f"Quick login failed for role: {role}. User not found or incorrect password.")
        return redirect("login")