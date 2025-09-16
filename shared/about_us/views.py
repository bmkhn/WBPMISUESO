from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required


def about_us_dispatcher(request):
	user = request.user
	if hasattr(user, 'role'):
		role = user.role
		if role in ["UESO", "DIRECTOR", "VP"]:
			return admin_about_us(request)
		elif role in ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
			return superuser_about_us(request)
		else:
			return user_about_us(request)
	return user_about_us(request)


def user_about_us(request):
	return render(request, 'about_us/user_about_us.html')


@login_required
@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"])
def superuser_about_us(request):
	return render(request, 'about_us/superuser_about_us.html')


@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def admin_about_us(request):
	return render(request, 'about_us/admin_about_us.html')

