from django.shortcuts import render
from system.users.decorators import user_confirmed

@user_confirmed
def home_view(request):
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False}
    return render(request, 'home/home.html', context)