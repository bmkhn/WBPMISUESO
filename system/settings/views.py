from django.shortcuts import render
from system.users.decorators import role_required

@role_required(allowed_roles=["UESO", "VP", "DIRECTOR"], require_confirmed=True)
def settings_view(request):
    """
    View for system settings management
    """
    base_template = 'base_internal.html'
    
    context = {
        'base_template': base_template,
    }
    
    return render(request, 'settings/settings.html', context)
