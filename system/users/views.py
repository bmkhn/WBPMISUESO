from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
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

import os, random
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from .models import User


def registration_faculty_view(request):
    error = None
    email = None
    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        if form.is_valid():
            code = str(random.randint(100000, 999999))
            email = form.cleaned_data['email']
            send_mail(
                'Your 2FA Verification Code',
                f'Your verification code is: {code}',
                'noreply@yourdomain.com',
                [email],
                fail_silently=False,
            )
            request.session['registration_data'] = form.cleaned_data
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

def faculty_verify_view(request):
    error = None
    email = None
    if request.method == 'POST':
        entered_code = request.POST.get('2fa_code')
        sent_code = request.session.get('2fa_code')
        data = request.session.get('registration_data')
        form = FacultyRegistrationForm(data) if data else FacultyRegistrationForm()
        if entered_code == sent_code and form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = User.Role.FACULTY
            user.is_confirmed = False
            user.save()
            request.session.pop('registration_data', None)
            request.session.pop('2fa_code', None)
            return redirect('registration_pending')
        else:
            error = "Invalid verification code. Please check your email and try again."
    return render(request, 'users/faculty_verify.html', {
        'error': error,
        'email': email,
    })
    
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



