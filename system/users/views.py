from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from system.users.models import College
from .forms import LoginForm, FacultyRegistrationForm
from django.contrib.auth import authenticate
from system.users.decorators import role_required

from django.contrib.auth import get_user_model      # For Creating Test Users (Delete Later)     

def login_view(request):
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

@login_required
def role_redirect(request):
    role = request.user.role
    
    if role in ["IMPLEMENTER", "CLIENT", "FACULTY"]:
        return redirect("home")
    else:
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

def register_view(request):
    return render(request, 'users/register.html')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Handle password reset logic here
    return render(request, 'users/forgot_password.html')




# Registration Views for Different User Types
def registration_client_view(request):
    return render(request, 'users/registration_client.html')

import random
from django.core.mail import send_mail

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
            return redirect('faculty_verify')
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

from .models import College

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
                username=registration_data['email'],  # Add this line
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


def thank_you_view(request):    
    return render(request, 'users/thank_you.html')

def registration_implementer_view(request):
    return render(request, 'users/registration_implementer.html')


















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



