
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required
from django.core.paginator import Paginator
from .models import Downloadable

def downloadable_dispatcher(request):
    user = request.user
    if hasattr(user, 'role'):
        role = user.role
        if role in ["UESO", "DIRECTOR", "VP"]:
            return admin_downloadable(request)
        elif role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
            return superuser_downloadable(request)
        else:
            return user_downloadable(request)
    return user_downloadable(request)

def user_downloadable(request):
    downloadables = Downloadable.objects.all().order_by('-id')
    paginator = Paginator(downloadables, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'downloadables/user_downloadable.html', {'page_obj': page_obj})

@login_required
@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"])
def superuser_downloadable(request):
    downloadables = Downloadable.objects.all().order_by('-id')
    paginator = Paginator(downloadables, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'downloadables/superuser_downloadable.html', {'page_obj': page_obj})

@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def admin_downloadable(request):
    downloadables = Downloadable.objects.all().order_by('-id')
    paginator = Paginator(downloadables, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'downloadables/admin_downloadable.html', {'page_obj': page_obj})



