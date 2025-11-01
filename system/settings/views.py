from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from system.users.decorators import role_required

# Cleaned up imports
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

# Define the roles that are considered "Admin" for settings management
ADMIN_ROLES = ["UESO", "VP", "DIRECTOR"]

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def settings_view(request):
    """
    Main view for system settings.
    This page will link to the different settings management sections.
    """
    base_template = 'base_internal.html'
    
    context = {
        'base_template': base_template,
    }
    
    return render(request, 'settings/settings.html', context)

# --- College CRUD Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_colleges(request):
    colleges = College.objects.all().order_by('name')
    context = {
        'base_template': 'base_internal.html',
        'colleges': colleges,
    }
    return render(request, 'settings/manage_colleges.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_college(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'College added successfully.')
            return redirect('system_settings:manage_colleges')
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
            return redirect('system_settings:manage_colleges')
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
        college.delete()
        messages.success(request, f'College "{college.name}" deleted successfully.')
        return redirect('system_settings:manage_colleges')
    
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': college,
        'confirm_message': f'Are you sure you want to delete the college "{college.name}"?'
    }
    return render(request, 'settings/confirm_delete.html', context)

# --- Campus CRUD Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_campus(request):
    """
    Lists all Campuses in the database.
    """
    campuses = Campus.objects.all()
    context = {
        'base_template': 'base_internal.html',
        'campuses': campuses,
    }
    return render(request, 'settings/manage_campus.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_campus(request):
    """
    Handles creating a new Campus.
    """
    if request.method == 'POST':
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus added successfully.')
            return redirect('system_settings:manage_campus')
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
    """
    Handles editing an existing Campus.
    """
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == 'POST':
        form = CampusForm(request.POST, instance=campus)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus updated successfully.')
            return redirect('system_settings:manage_campus')
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
    """
    Handles deleting a Campus.
    """
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == 'POST':
        campus.delete()
        messages.success(request, f'Campus "{campus.name}" deleted successfully.')
        return redirect('system_settings:manage_campus')

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': campus,
        'confirm_message': f'Are you sure you want to delete the campus "{campus.name}"? Colleges associated with it will lose this association.'
    }
    return render(request, 'settings/confirm_delete.html', context)

# --- SDG CRUD Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_sdgs(request):
    sdgs = SustainableDevelopmentGoal.objects.all().order_by('goal_number') # Changed order_by to goal_number
    context = {
        'base_template': 'base_internal.html',
        'sdgs': sdgs,
    }
    return render(request, 'settings/manage_sdgs.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_sdg(request):
    if request.method == 'POST':
        # Removed request.FILES since the model has no ImageField
        form = SDGForm(request.POST) 
        if form.is_valid():
            form.save()
            messages.success(request, 'SDG added successfully.')
            return redirect('system_settings:manage_sdgs')
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
        # Removed request.FILES
        form = SDGForm(request.POST, instance=sdg) 
        if form.is_valid():
            form.save()
            messages.success(request, 'SDG updated successfully.')
            return redirect('system_settings:manage_sdgs')
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
        sdg.delete()
        messages.success(request, f'SDG "{sdg.name}" deleted successfully.')
        return redirect('system_settings:manage_sdgs')
    
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': sdg,
        'confirm_message': f'Are you sure you want to delete the SDG "{sdg.name}"?'
    }
    return render(request, 'settings/confirm_delete.html', context)

# --- System Settings View ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_system_settings(request):
    # Ensure default settings exist
    defaults = {
        'site_name': ('WBPMIS UESO', 'The public name of the website.'),
        'maintenance_mode': ('False', 'Set to "True" to show a maintenance page to non-admins.'),
    }
    for key, (value, desc) in defaults.items():
        SystemSetting.objects.get_or_create(key=key, defaults={'value': value, 'description': desc})
    
    settings_objects = SystemSetting.objects.all()
    
    if request.method == 'POST':
        # Create a form for each setting, using the key as a prefix
        forms = [SystemSettingForm(request.POST, instance=s, prefix=s.key) for s in settings_objects]
        if all(f.is_valid() for f in forms):
            for f in forms:
                f.save()
            messages.success(request, 'System settings updated.')
            return redirect('system_settings:manage_system_settings')
    else:
        forms = [SystemSettingForm(instance=s, prefix=s.key) for s in settings_objects]
    
    # Zip settings with their forms for the template
    settings_with_forms = zip(settings_objects, forms)
    
    context = {
        'base_template': 'base_internal.html',
        'settings_with_forms': settings_with_forms,
    }
    return render(request, 'settings/manage_system_settings.html', context)

# --- Delete Account View ---

@login_required
def delete_account(request):
    user = request.user
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            if user.check_password(password):
                user_email = user.email # Get email before logging out
                user.delete() # This will permanently delete the user
                logout(request)
                messages.success(request, f'Your account ({user_email}) has been permanently deleted.')
              
                return redirect('home') 
            else:
                messages.error(request, 'Incorrect password. Account deletion failed.')
    else:
        form = DeleteAccountForm()
        
    context = {
        'base_template': 'base_internal.html', # Assumes user is logged in
        'form': form,
    }
    return render(request, 'settings/delete_account.html', context)

# --- API Key Management Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_api_keys(request):
    """
    Lists all API Keys and provides a button to add new ones.
    """
    keys = APIKey.objects.all().order_by('-created')
    context = {
        'base_template': 'base_internal.html',
        'keys': keys,
    }
    return render(request, 'settings/manage_api_keys.html', context)

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_api_key(request):
    """
    Handles the creation of a new API Key.
    """
    if request.method == 'POST':
        form = APIKeyForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            # create_key returns the model instance AND the plain-text key
            api_key, key = APIKey.objects.create_key(name=name)
            
            # CRITICAL: Show the key to the admin ONCE. It cannot be retrieved again.
            messages.warning(request, 
                f"<strong>API Key Generated!</strong><br>"
                f"The key for <strong>{api_key.name}</strong> has been created. "
                f"Please copy it now and store it securely.<br><br>"
                f"<strong>Key:</strong> <pre>{key}</pre><br>"
                f"You will <strong>NOT</strong> be able to see this key again.",
                extra_tags='safe' # Allows HTML in the message
            )
            return redirect('system_settings:manage_api_keys')
    else:
        form = APIKeyForm()
    
    context = {
        'base_template': 'base_internal.html',
        'form': form,
        'form_title': 'Generate New API Key'
    }
    return render(request, 'settings/form_template.html', context) # Re-use the form template

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def revoke_api_key(request, pk):
    """
    "Removes" an API key by revoking it. It is not deleted, just disabled.
    """
    api_key = get_object_or_404(APIKey, pk=pk)
    if request.method == 'POST':
        api_key.revoked = True
        api_key.save()
        messages.success(request, f'The API key "{api_key.name}" has been revoked and can no longer be used.')
        return redirect('system_settings:manage_api_keys')

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': api_key, # Re-use the delete template's context
        'confirm_message': f'Are you sure you want to revoke this API key? It will immediately stop working.',
        'confirm_button_text': 'Yes, Revoke Key'
    }
    return render(request, 'settings/confirm_delete.html', context) 