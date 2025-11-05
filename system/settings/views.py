from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from system.users.decorators import role_required
from datetime import datetime
from shared.budget.models import BudgetPool
from shared.budget.forms import AnnualBudgetForm
from system.users.models import College, User, Campus
from shared.projects.models import SustainableDevelopmentGoal
from rest_framework_api_key.models import APIKey
from .models import SystemSetting
from .forms import (
    CollegeForm, 
    SDGForm, 
    SystemSettingForm, 
    DeleteAccountForm, 
    APIKeyForm, 
    CampusForm
)

ADMIN_ROLES = ["UESO", "VP", "DIRECTOR"]

INTERNAL_ACCESS_ROLES = [
    "VP", 
    "DIRECTOR", 
    "UESO", 
    "PROGRAM_HEAD", 
    "DEAN", 
    "COORDINATOR",
    "FACULTY",
    "IMPLEMENTER",
    "CLIENT",
]

@role_required(allowed_roles=INTERNAL_ACCESS_ROLES, require_confirmed=True)
def settings_view(request):
    
    user = request.user
    user_role = getattr(user, 'role', None)
    is_admin = user_role in ADMIN_ROLES
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
        
    api_unlocked = request.session.get('api_unlocked', False)
    current_fiscal_year = str(datetime.now().year)
    
    budget_pool_instance, created = BudgetPool.objects.get_or_create(
        fiscal_year=current_fiscal_year,
        defaults={'total_available': '0.00'}
    )

    defaults = {
        'site_name': ('WBPMIS UESO', 'The public name of the website.'),
        'maintenance_mode': ('False', 'Set to "True" to show a maintenance page to non-admins.'),
    }
    for key, (value, desc) in defaults.items():
        SystemSetting.objects.get_or_create(key=key, defaults={'value': value, 'description': desc})
    
    settings_objects = SystemSetting.objects.all()

    if request.method == 'POST':
        if 'unlock_api' in request.POST:
            password = request.POST.get('api_password')
            if request.user.check_password(password):
                request.session['api_unlocked'] = True
                api_unlocked = True
                messages.success(request, 'API Management section unlocked.')
            else:
                request.session['api_unlocked'] = False
                messages.error(request, 'Incorrect password. API Management remains locked.')
            return redirect('system_settings:settings')

        elif 'save_general_settings' in request.POST:
            forms = [SystemSettingForm(request.POST, instance=s, prefix=s.key) for s in settings_objects]
            if all(f.is_valid() for f in forms):
                for f in forms:
                    f.save()
                messages.success(request, 'System settings updated.')
            else:
                messages.error(request, 'Failed to update settings. Please check the form for errors.')
            return redirect('system_settings:settings')
        
        elif 'save_annual_budget' in request.POST:
            budget_form = AnnualBudgetForm(request.POST) 
            if budget_form.is_valid():
                new_total = budget_form.cleaned_data['annual_total']
                budget_pool_instance.total_available = new_total
                budget_pool_instance.save(update_fields=['total_available'])
                messages.success(request, f'Annual Budget Pool for {budget_pool_instance.fiscal_year} updated successfully to ₱{new_total:,.2f}.')
            else:
                messages.error(request, 'Failed to update Annual Budget. Please check the form for errors.')
            return redirect('system_settings:settings')
    
    forms = [SystemSettingForm(instance=s, prefix=s.key) for s in settings_objects]
    settings_with_forms = zip(settings_objects, forms)
    
    budget_form = AnnualBudgetForm(initial={
        'fiscal_year': budget_pool_instance.fiscal_year,
        'annual_total': budget_pool_instance.total_available
    })

    colleges = College.objects.all().order_by('name')
    campuses = Campus.objects.all().order_by('name')
    sdgs = SustainableDevelopmentGoal.objects.all().order_by('goal_number')
    
    keys = []
    if api_unlocked:
        keys = APIKey.objects.all().order_by('-created')

    context = {
        'base_template': base_template,
        'admin': is_admin,
        'colleges': colleges,
        'campuses': campuses,
        'sdgs': sdgs,
        'keys': keys,
        'api_unlocked': api_unlocked,
        'settings_with_forms': settings_with_forms,
        'budget_pool': budget_pool_instance, 
        'budget_form': budget_form,         
    }
    
    return render(request, 'settings/settings.html', context)


@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_colleges(request):
    return redirect('system_settings:settings')

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_college(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'College added successfully.')
            return redirect('system_settings:settings')
    else:
        form = CollegeForm()
    
    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': 'Add New College'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def edit_college(request, pk):
    college = get_object_or_404(College, pk=pk)
    if request.method == 'POST':
        form = CollegeForm(request.POST, request.FILES, instance=college)
        if form.is_valid():
            form.save()
            messages.success(request, 'College updated successfully.')
            return redirect('system_settings:settings')
    else:
        form = CollegeForm(instance=college)
    
    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': f'Edit College: {college.name}'
    } 
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def delete_college(request, pk):
    college = get_object_or_404(College, pk=pk)
    if request.method == 'POST':
        college_name = college.name
        college.delete()
        messages.success(request, f'College "{college_name}" deleted successfully.')
        return redirect('system_settings:settings')
    
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': college,
        'confirm_message': f'Are you sure you want to delete the college "{college.name}"?',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_campus(request):
    return redirect('system_settings:settings') 

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_campus(request):
    if request.method == 'POST':
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus added successfully.')
            return redirect('system_settings:settings')
    else:
        form = CampusForm()

    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': 'Add New Campus'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def edit_campus(request, pk):
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == 'POST':
        form = CampusForm(request.POST, instance=campus)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus updated successfully.')
            return redirect('system_settings:settings')
    else:
        form = CampusForm(instance=campus)

    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': f'Edit Campus: {campus.name}'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def delete_campus(request, pk):
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == 'POST':
        campus_name = campus.name
        campus.delete()
        messages.success(request, f'Campus "{campus_name}" deleted successfully.')
        return redirect('system_settings:settings')

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': campus,
        'confirm_message': f'Are you sure you want to delete the campus "{campus.name}"? Colleges associated with it will lose this association.',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_sdgs(request):
    return redirect('system_settings:settings') 

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_sdg(request):
    if request.method == 'POST':
        form = SDGForm(request.POST) 
        if form.is_valid():
            form.save()
            messages.success(request, 'SDG added successfully.')
            return redirect('system_settings:settings')
    else:
        form = SDGForm()
    
    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': 'Add New SDG'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def edit_sdg(request, pk):
    sdg = get_object_or_404(SustainableDevelopmentGoal, pk=pk)
    if request.method == 'POST':
        form = SDGForm(request.POST, instance=sdg) 
        if form.is_valid():
            form.save()
            messages.success(request, 'SDG updated successfully.')
            return redirect('system_settings:settings')
    else:
        form = SDGForm(instance=sdg)
    
    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': f'Edit SDG: {sdg.name}'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def delete_sdg(request, pk):
    sdg = get_object_or_404(SustainableDevelopmentGoal, pk=pk)
    if request.method == 'POST':
        sdg_name = sdg.name
        sdg.delete()
        messages.success(request, f'SDG "{sdg_name}" deleted successfully.')
        return redirect('system_settings:settings')
    
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': sdg,
        'confirm_message': f'Are you sure you want to delete the SDG "{sdg.name}"?',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_system_settings(request):
    return redirect('system_settings:settings')

@login_required
def delete_account(request):
    user = request.user
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            if user.check_password(password):
                user_email = user.email
                user.delete()
                logout(request)
                messages.success(request, f'Your account ({user_email}) has been permanently deleted.')
              
                return redirect('home') 
            else:
                messages.error(request, 'Incorrect password. Account deletion failed.')
    else:
        form = DeleteAccountForm()
        
    context = {
        'base_template': 'base_internal.html',
        'form': form,
    }
    return render(request, 'settings/delete_account.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_api_keys(request):
    return redirect('system_settings:settings') 

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_api_key(request):
    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            api_key, key_string = APIKey.objects.create_key(name=name)
            
            context = {
                'base_template': 'base_internal.html',
                'api_key_name': api_key.name,
                'api_key_string': key_string,
            }
            return render(request, 'settings/show_api_key.html', context)
    else:
        form = APIKeyForm()
    
    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': 'Generate New API Key'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def revoke_api_key(request, pk):
    api_key = get_object_or_404(APIKey, pk=pk)
    if request.method == 'POST':
        api_key_name = api_key.name
        api_key.revoked = True
        api_key.save()
        messages.success(request, f'The API key "{api_key_name}" has been revoked and can no longer be used.')
        return redirect('system_settings:settings')

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': api_key,
        'confirm_message': f'Are you sure you want to revoke this API key? It will immediately stop working.',
        'confirm_button_text': 'Yes, Revoke Key',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)