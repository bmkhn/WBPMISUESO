from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from system.logs.models import LogEntry
from django.urls import reverse

class AboutUs(models.Model):
	hero_text = models.TextField(blank=False, null=False, default="Hero Text")
	vision_text = models.TextField(blank=False, null=False, default="Vision Text")
	mission_text = models.TextField(blank=False, null=False, default="Mission Text")
	thrust_text = models.TextField(blank=False, null=False, default="Thrust Text")
	leadership_description = models.TextField(blank=False, null=False, default="Leadership Description")
	director_name = models.CharField(max_length=255, blank=True, null=True, default="Director Name")
	director_image = models.ImageField(upload_to='about_us/director/', blank=True, null=True, default=None)
	org_chart_image = models.ImageField(upload_to='about_us/org_chart/', blank=True, null=True, default=None)
    
	edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='aboutus_edits')
	edited_at = models.DateTimeField(auto_now=True)


# Log creation and update actions for AboutUs
@receiver(post_save, sender=AboutUs)
def log_aboutus_action(sender, instance, created, **kwargs):
	user = instance.edited_by
	
	url = reverse('about_us_dispatcher')
	action = 'CREATE' if created else 'UPDATE'
	LogEntry.objects.create(
		user=user,
		action=action,
		model='AboutUs',
		object_id=instance.id,
		object_repr='About Us',
		details=f"Edited by: {instance.edited_by.get_full_name() if instance.edited_by else 'N/A'}",
		url=url,
		is_notification=False
	)
