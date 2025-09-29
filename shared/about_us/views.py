from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from system.users.decorators import role_required
from .models import AboutUs
from .forms import AboutUsForm
from django.utils import timezone

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
	about = AboutUs.objects.first()
	return render(request, 'about_us/user_about_us.html', {'about': about})

@login_required
@role_required(allowed_roles=["PROGRAM_HEAD", "DEAN", "COORDINATOR"])
def superuser_about_us(request):
	about = AboutUs.objects.first()
	return render(request, 'about_us/superuser_about_us.html', {'about': about})

@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def admin_about_us(request):
	about = AboutUs.objects.first()
	return render(request, 'about_us/admin_about_us.html', {'about': about})

@login_required
@role_required(allowed_roles=["UESO", "DIRECTOR", "VP"])
def edit_about_us(request):
	about = AboutUs.objects.first()

	if not about:
		about = AboutUs.objects.create()
	if request.method == 'POST':
		form = AboutUsForm(request.POST, request.FILES, instance=about)
		if form.is_valid():
			form.edited_by = request.user
			form.edited_at = timezone.now()
			form.save()
			return redirect('about_us_dispatcher')
	else:
		form = AboutUsForm(instance=about)
	return render(request, 'about_us/edit_about_us.html', {'about': about, 'form': form})