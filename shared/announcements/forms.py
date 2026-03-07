from django import forms
from .models import Announcement

class AnnouncementForm(forms.ModelForm):
	scheduled_at = forms.DateTimeField(
		required=False,
		input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'],
		widget=forms.DateTimeInput(
			attrs={'type': 'datetime-local'},
			format='%Y-%m-%dT%H:%M',
		),
	)

	class Meta:
		model = Announcement
		fields = [
			'title',
			'body',
			'scheduled_at',
			'cover_photo',
		]