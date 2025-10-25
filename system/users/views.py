from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
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
    logout(request)
    return render(request, 'users/register.html')

def registration_client_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST, request.FILES)

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

            # Create user with is_confirmed=False
            user = form.save(commit=False)
            user.is_confirmed = False
            user.username = user.email
            user.save()

            # Store only user id and 2fa code in session
            request.session['pending_user_id'] = user.id
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
        pending_user_id = request.session.get('pending_user_id')

        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.role = User.Role.CLIENT
                user.save()
            except User.DoesNotExist:
                error = "User not found. Please register again."
                return render(request, 'users/verify_client.html', {'error': error})
            # Optionally clear session data
            request.session.pop('pending_user_id', None)
            request.session.pop('2fa_code', None)
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
    return render(request, 'users/verify_client.html', {'error': error})


def registration_faculty_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST, request.FILES)

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

            # Create user with is_confirmed=False
            user = form.save(commit=False)
            user.is_confirmed = False
            user.username = user.email
            user.save()

            # Store only user id and 2fa code in session
            request.session['pending_user_id'] = user.id
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
        pending_user_id = request.session.get('pending_user_id')

        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.role = User.Role.FACULTY
                user.save()
            except User.DoesNotExist:
                error = "User not found. Please register again."
                return render(request, 'users/verify_faculty.html', {'error': error})
            # Optionally clear session data
            request.session.pop('pending_user_id', None)
            request.session.pop('2fa_code', None)
            return redirect('thank_you')
        else:
            error = "Invalid verification code. Please try again."
    return render(request, 'users/verify_faculty.html', {'error': error})


def registration_implementer_view(request):
    error = None
    email = None

    if request.method == 'POST':
        form = ImplementerRegistrationForm(request.POST, request.FILES)

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

            # Create user with is_confirmed=False
            user = form.save(commit=False)
            user.is_confirmed = False
            user.username = user.email
            user.role = user.Role.IMPLEMENTER
            user.save()

            # Store only user id and 2fa code in session
            request.session['pending_user_id'] = user.id
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
        pending_user_id = request.session.get('pending_user_id')

        if code_entered == code_sent and pending_user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=pending_user_id)
                user.role = User.Role.IMPLEMENTER
                user.save()
            except User.DoesNotExist:
                error = "User not found. Please register again."
                return render(request, 'users/verify_implementer.html', {'error': error})
            # Optionally clear session data
            request.session.pop('pending_user_id', None)
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

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

@role_required(allowed_roles=["VP", "DIRECTOR"])
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



@role_required(allowed_roles=["VP", "DIRECTOR"])
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
                )
                user.set_password(data.get('password', ''))
                user.save()

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
@role_required(allowed_roles=["VP", "DIRECTOR"])
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
        if User.objects.filter(email=data.get('email')).exclude(id=user.id).exists():
            error = "Email already exists."
        else:
            try:
                user.last_name = data.get('last_name')
                user.given_name = data.get('given_name')
                user.middle_initial = data.get('middle_initial') or None
                user.suffix = data.get('suffix') or None
                user.sex = data.get('sex')
                user.email = data.get('email')
                user.contact_no = data.get('contact_no')

                user.role = data.get('role')
                user.username = data.get('email')

                user.college = College.objects.get(id=data.get('college')) if data.get('college') else None
                user.campus = data.get('campus') if data.get('campus') else None
                user.degree = data.get('degree') or None
                user.expertise = data.get('expertise') or None
                user.company = data.get('company') or None
                user.industry = data.get('industry') or None

                # Only update password if provided and not blank
                password = data.get('password', '').strip()
                if password:
                    user.set_password(password)

                user.save()
                success = True
            except Exception as e:
                error = str(e)
    return render(request, 'users/edit_user.html', {
        'user': user,
        'error': error,
        'success': success,
        'colleges': colleges,
        'campus_choices': campus_choices,
        'roles': roles,
    })


# Verify/Unverify user views
from django.http import HttpResponseRedirect

@role_required(allowed_roles=["VP", "DIRECTOR"])
def verify_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    user.is_confirmed = True
    user.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@role_required(allowed_roles=["VP", "DIRECTOR"])
def unverify_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    user.is_confirmed = False
    user.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


from django.http import HttpResponseRedirect
from django.urls import reverse

# Delete user view with confirmation
@role_required(allowed_roles=["VP", "DIRECTOR"])
def delete_user(request, id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)
    user.delete()
    return HttpResponseRedirect(reverse('manage_user'))

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