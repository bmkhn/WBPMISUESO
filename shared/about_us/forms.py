from django import forms
from .models import AboutUs

class AboutUsForm(forms.ModelForm):
    class Meta:
        model = AboutUs
        fields = [
            'hero_text',
            'vision_text',
            'mission_text',
            'thrust_text',
            'leadership_description',
            'director_name',
            'director_image',
            'org_chart_image',
        ]