from django import forms
from .models import Announcement

class AnnouncementForm(forms.ModelForm):
	class Meta:
		model = Announcement
		fields = [
			'title',
			'body',
			'scheduled_at',
			'cover_photo',
		]