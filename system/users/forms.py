from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@yourdomain.com'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '********'
        })
    )


class UnifiedRegistrationForm(forms.ModelForm):
    """Unified registration form for Faculty, Implementer, and Client roles"""
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    
    class Meta:
        model = User
        fields = [
            'given_name', 'middle_initial', 'last_name', 'suffix', 'sex', 'email', 'contact_no',
            'college', 'degree', 'expertise', 'company', 'industry',
            'password', 'confirm_password', 'preferred_id', 'valid_id'
        ]
        # Note: 'campus' removed - derived from college.campus
    
    def __init__(self, *args, role=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = role
        
        # Make all optional fields not required initially
        # NOTE: campus removed - derived from college
        for field_name in ['middle_initial', 'suffix', 'college', 'degree', 
                          'expertise', 'company', 'industry', 'preferred_id', 'valid_id']:
            if field_name in self.fields:
                self.fields[field_name].required = False
        
        # Set required fields based on role
        if role == 'FACULTY':
            # NOTE: campus requirement removed - derived from college
            self.fields['college'].required = True
            self.fields['degree'].required = True
            self.fields['expertise'].required = True
        elif role == 'IMPLEMENTER':
            self.fields['degree'].required = True
            self.fields['expertise'].required = True
        elif role == 'CLIENT':
            self.fields['company'].required = True
            self.fields['industry'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        # Only validate password match if both are provided
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords Do Not Match.")
        
        # If only one password is provided, require both
        if (password and not confirm_password) or (confirm_password and not password):
            if password and not confirm_password:
                self.add_error('confirm_password', "Please confirm your password.")
            else:
                self.add_error('password', "Please enter your password.")
        
        return cleaned_data


# Keep old forms for backward compatibility (can be removed later)
class ClientRegistrationForm(UnifiedRegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, role='CLIENT', **kwargs)


class FacultyRegistrationForm(UnifiedRegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, role='FACULTY', **kwargs)


class ImplementerRegistrationForm(UnifiedRegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, role='IMPLEMENTER', **kwargs)