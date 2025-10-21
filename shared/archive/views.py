from django.shortcuts import render

# Create your views here.
def archive_view(request):

    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"

    context = {

        'base_template': base_template,
    }
    
    return render(request, 'archive/archive.html', context)