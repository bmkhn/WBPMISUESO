from django.shortcuts import render
from system.users.decorators import user_confirmed

# @login_required
# @role_required(allowed_roles=["VP", "DIRECTOR", "UESO", "COORDINATOR", "DEAN", "PROGRAM_HEAD"])
# def dashboard_view(request):
#     user_role = getattr(request.user, 'role', None)

#     vpde_content = user_role in ["VP", "DIRECTOR"]

#     return render(request, 'dashboard/dashboard.html', {
#         'user_role': user_role,
#         'vpde_content': vpde_content,
#     })

@user_confirmed
def home_view(request):
    if request.user.is_authenticated:
        context = {'is_user': True, 'user_role': getattr(request.user, 'role', None)}
    else:
        context = {'is_user': False}
    return render(request, 'home/home.html', context)