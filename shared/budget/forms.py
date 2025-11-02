# in shared/budget/forms.py
from django import forms
from .models import CollegeBudget, ExternalFunding
from shared.projects.models import Project
from system.users.models import College
from decimal import Decimal

class AnnualBudgetForm(forms.Form):
    """Form for the Admin to set the annual BudgetPool."""
    fiscal_year = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    annual_total = forms.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Set the total available budget pool for the entire fiscal year."
    )

class CollegeAllocationForm(forms.ModelForm):
    """Form for Admins to edit a single college's 'cut'."""
    class Meta:
        model = CollegeBudget
        fields = ['college', 'total_assigned', 'status', 'fiscal_year'] 

class ProjectInternalBudgetForm(forms.Form):
    """Form for College Admins to assign internal budget to a project."""
    project = forms.ModelChoiceField(queryset=Project.objects.none()) # Queryset set dynamically in the view
    internal_budget = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="The internal budget amount to assign to this project."
    )

class ExternalFundingEditForm(forms.ModelForm):
    """Form to create or edit an external funding record."""
    class Meta:
        model = ExternalFunding
        fields = [
            'sponsor_name', 'sponsor_contact', 'project', 
            'amount_offered', 'amount_received', 'status', 
            'proposal_date', 'created_by'
        ]
        widgets = {
            'proposal_date': forms.DateInput(attrs={'type': 'date'}),
        }