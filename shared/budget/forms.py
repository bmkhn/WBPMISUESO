from django import forms
from .models import BudgetAllocation, BudgetCategory, ExternalFunding
from system.users.models import College
from shared.projects.models import Project
from django.utils import timezone

class BudgetAllocationEditForm(forms.ModelForm):
    """Form for editing budget allocations"""
    
    class Meta:
        model = BudgetAllocation
        fields = [
            'college', 'project', 'category', 'total_assigned', 
            'total_remaining', 'total_spent', 'quarter', 
            'fiscal_year', 'status'
        ]
        widgets = {
            'college': forms.Select(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'total_assigned': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_remaining': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_spent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quarter': forms.TextInput(attrs={'class': 'form-control'}),
            'fiscal_year': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['college'].queryset = College.objects.all()
        self.fields['project'].queryset = Project.objects.all()
        self.fields['category'].queryset = BudgetCategory.objects.all()
        
        # Make college and project optional
        self.fields['college'].required = False
        self.fields['project'].required = False

class ExternalFundingEditForm(forms.ModelForm):
    """Form for editing external funding"""
    
    class Meta:
        model = ExternalFunding
        fields = [
            'sponsor_name', 'sponsor_contact', 'project', 
            'amount_offered', 'amount_received', 'status',
            'proposal_date', 'expected_completion'
        ]
        widgets = {
            'sponsor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sponsor_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'amount_offered': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount_received': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'proposal_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_completion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.all()

class BudgetSearchForm(forms.Form):
    """Form for searching and filtering budgets"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by college, project, or category...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + BudgetAllocation.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quarter = forms.ChoiceField(
        choices=[('', 'All Quarters')] + [
            (f'Q{i}-2024', f'Q{i} 2024') for i in range(1, 5)
        ] + [
            (f'Q{i}-2025', f'Q{i} 2025') for i in range(1, 5)
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class DynamicBudgetAllocationForm(forms.Form):
    """Form for dynamically allocating budgets to colleges"""
    college = forms.ModelChoiceField(
        queryset=College.objects.all(),
        empty_label="Select College",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'college-select',
            'required': True
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=BudgetCategory.objects.all(),
        empty_label="Select Category",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'category-select',
            'required': True
        })
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'amount-input',
            'step': '0.01',
            'placeholder': 'Enter amount to allocate',
            'required': True
        })
    )
    
    quarter = forms.CharField(
        initial=lambda: f"Q{((timezone.now().month - 1) // 3) + 1}-{timezone.now().year}",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'quarter-input',
            'readonly': True
        })
    )
    
    fiscal_year = forms.CharField(
        initial=lambda: str(timezone.now().year),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'fiscal-year-input',
            'readonly': True
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description for this allocation'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        current_quarter = f"Q{((timezone.now().month - 1) // 3) + 1}-{timezone.now().year}"
        current_year = str(timezone.now().year)
        
        self.fields['quarter'].initial = current_quarter
        self.fields['fiscal_year'].initial = current_year
