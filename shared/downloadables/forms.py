from django import forms
from .models import Downloadable

class DownloadableForm(forms.ModelForm):
    class Meta:
        model = Downloadable
        fields = ['file', 'available_for_non_users']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'required': True}),
            'available_for_non_users': forms.CheckboxInput(),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('File is required.')
        return file