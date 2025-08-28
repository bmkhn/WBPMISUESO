from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required

@login_required
@role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
def inbox_view(request):
    return render(request, 'inbox/inbox.html')

# @login_required
# @role_required(allowed_roles=["VP", "DIRECTOR", "UESO"])
# def inbox_detail(request, inbox_id):
#     return render(request, 'inbox/inbox_detail.html', {'inbox_id': inbox_id})