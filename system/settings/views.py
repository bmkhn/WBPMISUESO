from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce 
from decimal import Decimal 
from system.users.decorators import role_required
from datetime import datetime
from shared.budget.models import BudgetPool, BudgetHistory, CollegeBudget
from shared.budget.forms import AnnualBudgetForm
from system.users.models import College, User, Campus
from shared.projects.models import SustainableDevelopmentGoal
from rest_framework_api_key.models import APIKey
from shared.projects.models import ProjectType 
from shared.projects.forms import ProjectTypeForm
from .models import SystemSetting, APIConnection
from .forms import (
    CollegeForm, 
    SDGForm, 
    SystemSettingForm, 
    DeleteAccountForm, 
    APIKeyForm, 
    CampusForm,
    APIConnectionRequestForm
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

# Roles allowed to REQUEST keys 
API_ACCESS_ROLES = [
    "PROGRAM_HEAD", 
    "DEAN", 
    "COORDINATOR",
    "FACULTY",
    "IMPLEMENTER",
    "CLIENT",
]

def _log_budget_pool_history(user, pool_instance, new_total, is_creation):
    action_type = 'ALLOCATED' if is_creation else 'ADJUSTED'
    description_str = f'Annual Budget Pool initialized/set for {pool_instance.fiscal_year}: ₱{new_total:,.2f}'
    
    BudgetHistory.objects.create(
        action=action_type,
        amount=new_total, 
        description=description_str,
        user=user
    )

@role_required(allowed_roles=INTERNAL_ACCESS_ROLES, require_confirmed=True)
def settings_view(request):
    
    user = request.user
    user_role = getattr(user, 'role', None)
    is_admin = user_role in ADMIN_ROLES
    is_api_user = user_role in API_ACCESS_ROLES
    
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
        
    api_unlocked = request.session.get('api_unlocked', False)
    current_fiscal_year = str(datetime.now().year)
    
    # --- Budget Logic ---
    budget_pool_instance, created = BudgetPool.objects.get_or_create(
        fiscal_year=current_fiscal_year,
        defaults={'total_available': Decimal('0.00')}
    )
    current_pool_total = budget_pool_instance.total_available
    total_assigned_aggregate = CollegeBudget.objects.filter(
        fiscal_year=current_fiscal_year,
        status='ACTIVE'
    ).aggregate(total=Coalesce(Sum('total_assigned'), Value(Decimal('0.00'))))
    total_assigned_budget = total_assigned_aggregate['total']
    initial_unallocated_remaining = budget_pool_instance.total_available - total_assigned_budget
    is_save_disabled = initial_unallocated_remaining < 0

    # --- General Settings Logic ---
    defaults = {
        'site_name': ('WBPMIS UESO', 'The public name of the website.'),
        'maintenance_mode': ('False', 'Set to "True" to show a maintenance page to non-admins.'),
    }
    for key, (value, desc) in defaults.items():
        SystemSetting.objects.get_or_create(key=key, defaults={'value': value, 'description': desc})
    
    settings_objects = SystemSetting.objects.all()

    # --- POST Handling ---
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
                new_total_str = budget_form.cleaned_data['annual_total']
                new_total = Decimal(new_total_str)
                is_changed = new_total != current_pool_total
                
                if new_total < total_assigned_budget:
                    messages.error(
                        request, 
                        f'The Annual Budget Pool (₱{new_total:,.2f}) cannot be set lower than the total amount already assigned to colleges (₱{total_assigned_budget:,.2f}).'
                    )
                else:
                    is_creation = current_pool_total == Decimal('0.00')
                    if is_changed or is_creation:
                        budget_pool_instance.total_available = new_total
                        budget_pool_instance.save(update_fields=['total_available'])
                        _log_budget_pool_history(request.user, budget_pool_instance, new_total, is_creation)
                        messages.success(request, f'Annual Budget Pool for {budget_pool_instance.fiscal_year} updated successfully to ₱{new_total:,.2f}.')
                    else:
                        messages.info(request, "Annual Budget Pool value did not change.")
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
    project_types = ProjectType.objects.all().order_by('name')
    
    # --- API Connection Logic ---
    api_connections = []
    
    # Admins see ALL connections (if unlocked)
    if is_admin:
        if api_unlocked:
            api_connections = APIConnection.objects.all().order_by('-created_at')
    
    # Regular API Users see ONLY THEIR OWN connections
    elif is_api_user:
        api_connections = APIConnection.objects.filter(requested_by=user).order_by('-created_at')

    context = {
        'base_template': base_template,
        'admin': is_admin,
        'colleges': colleges,
        'campuses': campuses,
        'sdgs': sdgs,
        'api_connections': api_connections,
        'api_unlocked': api_unlocked,
        'settings_with_forms': settings_with_forms,
        'budget_pool': budget_pool_instance, 
        'budget_form': budget_form,   
        'total_assigned_budget': total_assigned_budget,
        'initial_unallocated_remaining': initial_unallocated_remaining,
        'is_save_disabled': is_save_disabled,
        'project_types': project_types,
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
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': 'Add New College'}
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
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': f'Edit College: {college.name}'} 
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
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': 'Add New Campus'}
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
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': f'Edit Campus: {campus.name}'}
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
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': 'Add New SDG'}
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
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': f'Edit SDG: {sdg.name}'}
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
    context = {'base_template': 'base_internal.html', 'form': form}
    return render(request, 'settings/delete_account.html', context)

# ==========================================
# New API Management Views
# ==========================================

# Updated to ONLY allow API_ACCESS_ROLES 
@role_required(allowed_roles=API_ACCESS_ROLES, require_confirmed=True)
def request_api_access(request):
    """Allows a user to request a new API connection."""
    if request.method == 'POST':
        form = APIConnectionRequestForm(request.POST)
        if form.is_valid():
            connection = form.save(commit=False)
            connection.requested_by = request.user
            connection.status = 'PENDING'
            connection.save()
            messages.success(request, 'API Connection request submitted. Please wait for administrator approval.')
            return redirect('system_settings:settings')
    else:
        form = APIConnectionRequestForm()
    
    if request.user.role in ['FACULTY', 'CLIENT', 'IMPLEMENTER']:
        base_template = 'base_public.html'
    else:
        base_template = 'base_internal.html'

    context = {
        'base_template': base_template,
        'form': form,
        'form_title': 'Request API Access'
    }
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def approve_api_access(request, pk):
    """Approves a pending request, generates the key, and stores it."""
    connection = get_object_or_404(APIConnection, pk=pk)
    
    if request.method == 'POST':
        api_key, key_string = APIKey.objects.create_key(name=connection.name)
        
        selected_tier = request.POST.get('tier', 'TIER_1')

        connection.api_key = api_key
        connection.full_api_key_string = key_string 
        connection.status = 'ACTIVE'
        connection.tier = selected_tier
        connection.save()
        
        context = {
            'base_template': 'base_internal.html',
            'api_key_name': connection.name,
            'api_key_string': key_string,
        }
        return render(request, 'settings/show_api_key.html', context)
        
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': connection, 
        'confirm_message': f'Approve access for "{connection.name}"?',
        'confirm_button_text': 'Yes, Approve & Generate Key',
        'cancel_url': reverse('system_settings:settings'),
        'show_tier_select': True, 
        'tier_choices': APIConnection.TIER_CHOICES,
    }
    return render(request, 'settings/confirm_delete.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def disconnect_api_access(request, pk):
    """Pauses/Revokes access without deleting the connection record."""
    connection = get_object_or_404(APIConnection, pk=pk)
    
    if request.method == 'POST':
        if connection.api_key:
            connection.api_key.revoked = True
            connection.api_key.save()
        
        connection.status = 'DISCONNECTED'
        connection.save()
        messages.success(request, f'Connection "{connection.name}" has been disconnected.')
        return redirect('system_settings:settings')

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': connection,
        'confirm_message': f'Are you sure you want to disconnect "{connection.name}"? The key will stop working immediately.',
        'confirm_button_text': 'Yes, Disconnect',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def delete_api_connection(request, pk):
    """Permanently deletes the connection record."""
    connection = get_object_or_404(APIConnection, pk=pk)
    if request.method == 'POST':
        name = connection.name
        if connection.api_key:
            connection.api_key.delete()
        connection.delete()
        messages.success(request, f'Connection "{name}" deleted permanently.')
        return redirect('system_settings:settings')
        
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': connection,
        'confirm_message': f'Are you sure you want to permanently delete the record for "{connection.name}"?',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)

# Project Type New CRUD
@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_project_types(request):
    return redirect('system_settings:settings') 

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_project_type(request):
    if request.method == 'POST':
        form = ProjectTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project Type added successfully.')
            return redirect('system_settings:settings')
    else:
        form = ProjectTypeForm()
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': 'Add New Project Type'}
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def edit_project_type(request, pk):
    pt = get_object_or_404(ProjectType, pk=pk)
    if request.method == 'POST':
        form = ProjectTypeForm(request.POST, instance=pt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project Type updated successfully.')
            return redirect('system_settings:settings')
    else:
        form = ProjectTypeForm(instance=pt)
    context = {'base_template': 'base_internal.html', 'form': form, 'form_title': f'Edit Project Type: {pt.name}'}
    return render(request, 'settings/form_template.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def delete_project_type(request, pk):
    pt = get_object_or_404(ProjectType, pk=pk)
    if request.method == 'POST':
        name = pt.name
        pt.delete()
        messages.success(request, f'Project Type "{name}" deleted successfully.')
        return redirect('system_settings:settings')
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': pt,
        'confirm_message': f'Are you sure you want to delete the project type "{pt.name}"?',
        'cancel_url': reverse('system_settings:settings')
    }
    return render(request, 'settings/confirm_delete.html', context)