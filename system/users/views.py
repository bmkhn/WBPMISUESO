from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, LoginForm
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
    
    if role in ["PUBLIC", "CLIENT", "FACULTY"]:
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

def registration_client_view(request):
    return render(request, 'users/registration_client.html')

def registration_faculty_view(request):
    return render(request, 'users/registration_faculty.html')

def registration_implementer_view(request):
    return render(request, 'users/registration_implementer.html')



# Quick Login View for Testing Purposes
User = get_user_model()

def quick_login(request, role):
    from django.contrib.auth import login
    from django.contrib.auth import authenticate

    # Assume your placeholder users are named like 'public', 'client', etc.
    username = f"{role.lower()}@example.com"
    password = "test1234"  # placeholder pass for all test users
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return redirect("role_redirect")
    else:
        return redirect("login")  # or error page
    


