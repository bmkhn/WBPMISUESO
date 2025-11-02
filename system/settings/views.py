from django.shortcuts import render, redirect, get_object_or_404
# FIX: Import 'reverse' to fix the NameError
from django.urls import reverse
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

# -------------------------------------------------------------------
# MODIFIED UNIFIED VIEW
# -------------------------------------------------------------------
@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def settings_view(request):
    """
    Main UNIFIED view for system settings.
    This page will now display all settings components.
    """
    base_template = 'base_internal.html'
    
    # Check for API password submission
    api_unlocked = request.session.get('api_unlocked', False)
    
    # --- FIX: Load General Settings data ---
    # Ensure default settings exist
    defaults = {
        'site_name': ('WBPMIS UESO', 'The public name of the website.'),
        'maintenance_mode': ('False', 'Set to "True" to show a maintenance page to non-admins.'),
    }
    for key, (value, desc) in defaults.items():
        SystemSetting.objects.get_or_create(key=key, defaults={'value': value, 'description': desc})
    
    settings_objects = SystemSetting.objects.all()
    # --- End of General Settings data load ---

    # --- FIX: Updated POST handling ---
    if request.method == 'POST':
        # Check if the API unlock form was submitted
        if 'unlock_api' in request.POST:
            password = request.POST.get('api_password')
            if request.user.check_password(password):
                request.session['api_unlocked'] = True
                api_unlocked = True
                messages.success(request, 'API Management section unlocked.')
            else:
                request.session['api_unlocked'] = False # Ensure it's false on failure
                messages.error(request, 'Incorrect password. API Management remains locked.')
            
            # Redirect to the same page to clear the POST data and show the message
            return redirect('system_settings:settings')

        # Check if the General Settings form was submitted
        elif 'save_general_settings' in request.POST:
            # Create a form for each setting, using the key as a prefix
            forms = [SystemSettingForm(request.POST, instance=s, prefix=s.key) for s in settings_objects]
            if all(f.is_valid() for f in forms):
                for f in forms:
                    f.save()
                messages.success(request, 'System settings updated.')
            else:
                messages.error(request, 'Failed to update settings. Please check the form for errors.')
            
            # Redirect to the same page to show messages
            return redirect('system_settings:settings')
    
    # --- END of POST handling ---

    # Create forms for GET request (to display the form)
    forms = [SystemSettingForm(instance=s, prefix=s.key) for s in settings_objects]
    # Zip settings with their forms for the template
    settings_with_forms = zip(settings_objects, forms)


    # Fetch all data for the unified page
    colleges = College.objects.all().order_by('name')
    campuses = Campus.objects.all().order_by('name')
    sdgs = SustainableDevelopmentGoal.objects.all().order_by('goal_number')
    
    # Only fetch keys if the section is unlocked
    keys = []
    if api_unlocked:
        keys = APIKey.objects.all().order_by('-created')

    context = {
        'base_template': base_template,
        'colleges': colleges,
        'campuses': campuses,
        'sdgs': sdgs,
        'keys': keys,
        'api_unlocked': api_unlocked,
        # FIX: Pass the settings forms to the template
        'settings_with_forms': settings_with_forms,
    }
    
    return render(request, 'settings/settings.html', context)

# -------------------------------------------------------------------
# ALL OTHER ORIGINAL VIEWS (Required for CRUD operations)
# -------------------------------------------------------------------

# --- College CRUD Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_colleges(request):
    # return render(request, 'settings/manage_colleges.html', context)
    return redirect('system_settings:settings') # Redirect to the new main page


@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_college(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'College added successfully.')
            return redirect('system_settings:settings') # Redirect to main settings
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
            return redirect('system_settings:settings') # Redirect to main settings
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
        return redirect('system_settings:settings') # Redirect to main settings
    
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': college,
        'confirm_message': f'Are you sure you want to delete the college "{college.name}"?',
        'cancel_url': reverse('system_settings:settings') # Add cancel URL
    }
    return render(request, 'settings/confirm_delete.html', context)

# --- Campus CRUD Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_campus(request):
    """
    Lists all Campuses in the database.
    """
    # This view is no longer directly browsed to.
    return redirect('system_settings:settings') 

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
            return redirect('system_settings:settings') # Redirect to main settings
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
            return redirect('system_settings:settings') # Redirect to main settings
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
        campus_name = campus.name
        campus.delete()
        messages.success(request, f'Campus "{campus_name}" deleted successfully.')
        return redirect('system_settings:settings') # Redirect to main settings

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': campus,
        'confirm_message': f'Are you sure you want to delete the campus "{campus.name}"? Colleges associated with it will lose this association.',
        'cancel_url': reverse('system_settings:settings') # Add cancel URL
    }
    return render(request, 'settings/confirm_delete.html', context)

# --- SDG CRUD Views ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_sdgs(request):
    # This view is no longer directly browsed to.
    return redirect('system_settings:settings') 

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def add_sdg(request):
    if request.method == 'POST':
        # Removed request.FILES since the model has no ImageField
        form = SDGForm(request.POST) 
        if form.is_valid():
            form.save()
            messages.success(request, 'SDG added successfully.')
            return redirect('system_settings:settings') # Redirect to main settings
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
            return redirect('system_settings:settings') # Redirect to main settings
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
        return redirect('system_settings:settings') # Redirect to main settings
    
    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': sdg,
        'confirm_message': f'Are you sure you want to delete the SDG "{sdg.name}"?',
        'cancel_url': reverse('system_settings:settings') # Add cancel URL
    }
    return render(request, 'settings/confirm_delete.html', context)

# --- System Settings View ---

@role_required(allowed_roles=ADMIN_ROLES, require_confirmed=True)
def manage_system_settings(request):
    # --- FIX: This view is no longer used, redirect to main settings ---
    return redirect('system_settings:settings')

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
    # This view is no longer directly browsed to.
    return redirect('system_settings:settings') 

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
            api_key, key_string = APIKey.objects.create_key(name=name)
            
            context = {
                'base_template': 'base_internal.html',
                'api_key_name': api_key.name,
                'api_key_string': key_string, # The full, plain-text key
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
    """
    "Removes" an API key by revoking it. It is not deleted, just disabled.
    """
    api_key = get_object_or_404(APIKey, pk=pk)
    if request.method == 'POST':
        api_key_name = api_key.name
        api_key.revoked = True
        api_key.save()
        messages.success(request, f'The API key "{api_key_name}" has been revoked and can no longer be used.')
        return redirect('system_settings:settings') # Redirect to main settings

    context = {
        'base_template': 'base_internal.html',
        'object_to_delete': api_key, # Re-use the delete template's context
        'confirm_message': f'Are you sure you want to revoke this API key? It will immediately stop working.',
        'confirm_button_text': 'Yes, Revoke Key',
        'cancel_url': reverse('system_settings:settings') # Add cancel URL
    }
    return render(request, 'settings/confirm_delete.html', context)

