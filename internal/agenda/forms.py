from django import forms
from .models import Agenda
from system.users.models import College

class AgendaForm(forms.ModelForm):
    concerned_colleges = forms.ModelMultipleChoiceField(
        queryset=College.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Concerned Colleges'
    )

    class Meta:
        model = Agenda
        fields = ['name', 'description', 'concerned_colleges']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input form-textarea'}),
        }
