from django.shortcuts import render
from system.users.decorators import role_required


def get_role_constants():
    INTERNAL_ROLES = ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    INTERNAL_WITH_COLLEGE_ROLES = ["PROGRAM_HEAD", "DEAN", "COORDINATOR"]
    FACULTY_ROLES = ["FACULTY", "IMPLEMENTER"]
    return INTERNAL_ROLES, INTERNAL_WITH_COLLEGE_ROLES, FACULTY_ROLES

def get_templates(request):
    user_role = getattr(request.user, 'role', None)
    if user_role in ["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR"]:
        base_template = "base_internal.html"
    else:
        base_template = "base_public.html"
    return base_template


################################################################################################################################################################


@role_required(["VP", "DIRECTOR", "UESO", "PROGRAM_HEAD", "DEAN", "COORDINATOR", "FACULTY", "IMPLEMENTER"])
def budget_dispatcher(request):
    INTERNAL_ROLES, INTERNAL_WITH_COLLEGE_ROLES, FACULTY_ROLES = get_role_constants()

    user_role = getattr(request.user, 'role', None)
    if user_role in INTERNAL_ROLES:
        return budget_internal_view(request)
    elif user_role in INTERNAL_WITH_COLLEGE_ROLES:
        return budget_internal_college_view(request)
    elif user_role in FACULTY_ROLES:
        return budget_faculty_view(request)


################################################################################################################################################################


def budget_faculty_view(request):
    context = {
        "base_template": get_templates(request),
    }
    return render(request, 'budget/faculty_budget.html', context)

def budget_internal_view(request):
    context = {
        "base_template": get_templates(request),
    }
    return render(request, 'budget/internal_budget.html', context)

def budget_internal_college_view(request):
    context = {
        "base_template": get_templates(request),
    }
    return render(request, 'budget/internal_college_budget.html', context)