from django import forms
from .models import Project, ProjectEvent


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'project_leader', 'agenda', 'project_type',
            'estimated_events', 'estimated_trainees', 'primary_beneficiary', 'primary_location',
            'logistics_type', 'internal_budget', 'external_budget', 'sponsor_name',
            'start_date', 'estimated_end_date'
        ]

class ProjectEventForm(forms.ModelForm):
    class Meta:
        model = ProjectEvent
        fields = ['title', 'description']
        

from django import forms
from .models import Project, ProjectEvent, FacultyExpense 
class FacultyExpenseForm(forms.ModelForm):
    class Meta:
        model = FacultyExpense
        # Exclude fields automatically set in the view
        fields = ['reason', 'amount', 'notes', 'receipt']
        widgets = {
            'reason': forms.TextInput(attrs={'placeholder': 'e.g., Transportation'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '100.00'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional details'}),
            # Ensure user sees only image uploads are allowed
            'receipt': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
        labels = { # Optional: Define labels directly here
            'reason': "Reason for Expense",
            'amount': "Amount (₱)",
            'notes': "Notes",
            'receipt': "Upload Receipt (Image Only)"
        }

    # Add validation if needed (like checking amount > 0)
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount