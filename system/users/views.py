from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

from system.users.models import College
from system.users.decorators import role_required
from .forms import LoginForm, ClientRegistrationForm, FacultyRegistrationForm, ImplementerRegistrationForm

import random

####################################################################################################

# Login, Logout, Forgot Password, and Role-Based Redirection Views
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
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def forgot_password_view(request):
    logout(request)
    if request.method == 'POST':
        email = request.POST.get('email')
        # Handle password reset logic here
    return render(request, 'users/forgot_password.html')

def role_redirect(request):
    role = getattr(request.user, 'role', None)
        
    if role in ["IMPLEMENTER", "CLIENT", "FACULTY"]:
        return redirect("home")
    elif role in ["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"]:
        return redirect("dashboard")

@login_required
def home(request):
    return render(request, 'base_public.html')  # extends base_public.html

@login_required
def dashboard(request):
    return render(request, 'base_internal.html')  # extends base_internal.html

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR"])
def manage_user(request):
    return render(request, 'users/manage_user.html')

####################################################################################################

# Registration Views for Different User Types

def register_view(request):
    logout(request)
    return render(request, 'users/register.html')

def registration_client_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)

        if form.is_valid() and not error:
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            send_mail(
                'Your 2FA Verification Code',
                f'Your verification code is: {code}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )

            registration_data = form.cleaned_data.copy()
            request.session['registration_data'] = registration_data
            request.session['2fa_code'] = code
            return redirect('verify_client')
        else:
            return render(request, 'users/registration_client.html', {
                'form': form,
                'error': error,
                'email': email,
            })
    else:
        form = ClientRegistrationForm()
        return render(request, 'users/registration_client.html', {
            'form': form,
            'error': error,
            'email': email,
        })  

def client_verify_view(request):
    error = None
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        registration_data = request.session.get('registration_data')

        if code_entered == code_sent and registration_data:
            User = get_user_model()
            user = User.objects.create_user(
                username=registration_data['email'],
                email=registration_data['email'],
                password=registration_data['password'],
                given_name=registration_data['given_name'],
                middle_initial=registration_data.get('middle_initial', ''),
                last_name=registration_data['last_name'],
                sex=registration_data['sex'],
                contact_no=registration_data['contact_no'],
                company=registration_data['company'],
                industry=registration_data['industry'],
                role=User.Role.CLIENT,
                is_confirmed=False,
            )
            # Optionally clear session data
            request.session.pop('registration_data', None)
            request.session.pop('2fa_code', None)
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
    return render(request, 'users/verify_client.html', {'error': error})


def registration_faculty_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        
        if form.is_valid() and not error:
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            send_mail(
                'Your 2FA Verification Code',
                f'Your verification code is: {code}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            # Save all registration data and preferred_id in session for later verification
            registration_data = form.cleaned_data.copy()
            college_instance = form.cleaned_data['college']
            registration_data['college'] = college_instance.id  # Store the ID instead of the instance
            request.session['registration_data'] = registration_data
            request.session['2fa_code'] = code
            return redirect('verify_faculty')
        else:
            return render(request, 'users/registration_faculty.html', {
                'form': form,
                'error': error,
                'email': email,
            })
    else:
        form = FacultyRegistrationForm()
        return render(request, 'users/registration_faculty.html', {
            'form': form,
            'error': error,
            'email': email,
        })


def faculty_verify_view(request):
    error = None
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        registration_data = request.session.get('registration_data')
        college_obj = College.objects.get(pk=registration_data['college'])

        if code_entered == code_sent and registration_data:
            User = get_user_model()
            user = User.objects.create_user(
                username=registration_data['email'],
                email=registration_data['email'],
                password=registration_data['password'],
                given_name=registration_data['given_name'],
                middle_initial=registration_data.get('middle_initial', ''),
                last_name=registration_data['last_name'],
                sex=registration_data['sex'],
                contact_no=registration_data['contact_no'],
                campus=registration_data['campus'],
                college=college_obj,
                degree=registration_data['degree'],
                expertise=registration_data['expertise'],
                role=User.Role.FACULTY,
                is_confirmed=False,
            )
            # Optionally clear session data
            request.session.pop('registration_data', None)
            request.session.pop('2fa_code', None)
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
    return render(request, 'users/verify_faculty.html', {'error': error})


def registration_implementer_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = ImplementerRegistrationForm(request.POST)
        
        if form.is_valid() and not error:
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            send_mail(
                'Your 2FA Verification Code',
                f'Your verification code is: {code}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            # Save all registration data and preferred_id in session for later verification
            registration_data = form.cleaned_data.copy()
            request.session['registration_data'] = registration_data
            request.session['2fa_code'] = code
            return redirect('verify_implementer')
        else:
            return render(request, 'users/registration_implementer.html', {
                'form': form,
                'error': error,
                'email': email,
            })
    else:
        form = ImplementerRegistrationForm()
        return render(request, 'users/registration_implementer.html', {
            'form': form,
            'error': error,
            'email': email,
        })


def implementer_verify_view(request):
    error = None
    if request.method == 'POST':
        code_entered = request.POST.get('verification_code')
        code_sent = request.session.get('2fa_code')
        registration_data = request.session.get('registration_data')

        if code_entered == code_sent and registration_data:
            User = get_user_model()
            user = User.objects.create_user(
                username=registration_data['email'],
                email=registration_data['email'],
                password=registration_data['password'],
                given_name=registration_data['given_name'],
                middle_initial=registration_data.get('middle_initial', ''),
                last_name=registration_data['last_name'],
                sex=registration_data['sex'],
                contact_no=registration_data['contact_no'],
                degree=registration_data['degree'],
                expertise=registration_data['expertise'],
                role=User.Role.IMPLEMENTER,
                is_confirmed=False,
            )
            # Optionally clear session data
            request.session.pop('registration_data', None)
            request.session.pop('2fa_code', None)
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
    return render(request, 'users/verify_implementer.html', {'error': error})


def thank_you_view(request):    
    return render(request, 'users/thank_you.html')

####################################################################################################

def not_authenticated_view(request):
    return render(request, 'users/403_not_authenticated.html', status=403)

def no_permission_view(request):
    return render(request, 'users/403_no_permission.html', status=403)

def not_confirmed_view(request):
    return render(request, 'users/403_not_confirmed.html', status=403)





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
        return redirect("login")  # or error page



