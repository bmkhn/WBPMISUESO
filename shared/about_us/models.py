from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from system.logs.models import LogEntry
from django.urls import reverse
from django.templatetags.static import static

class AboutUs(models.Model):
	hero_text = models.TextField(
		blank=False, 
		null=False, 
		default="Welcome to the University Extension Services Office (UESO). We are dedicated to fostering community engagement and extending the university's knowledge and resources to serve society."
	)
	vision_text = models.TextField(
		blank=False, 
		null=False, 
		default="To be a leading center of excellence in university extension services, creating meaningful partnerships between the academe and the community for sustainable development."
	)
	mission_text = models.TextField(
		blank=False, 
		null=False, 
		default="To deliver innovative extension programs and services that address community needs, promote social responsibility, and contribute to nation-building through collaborative partnerships and knowledge sharing."
	)
	thrust_text = models.TextField(
		blank=False, 
		null=False, 
		default="Our strategic thrust focuses on community empowerment, sustainable development, technology transfer, and capacity building to create lasting positive impact in the communities we serve."
	)
	leadership_description = models.TextField(
		blank=False, 
		null=False, 
		default="Our leadership team is committed to excellence in extension services, guided by principles of integrity, innovation, and inclusive development. We work collaboratively to ensure that university resources reach and benefit the wider community."
	)
	director_name = models.CharField(max_length=255, blank=True, null=True, default="Dr. Liezl F. Tangonan")
	director_image = models.ImageField(upload_to='about_us/director/', blank=True, null=True, default='faker/image.png')
	org_chart_image = models.ImageField(upload_to='about_us/org_chart/', blank=True, null=True, default='faker/UESO ORG CHART.png')
    
	edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='aboutus_edits')
	edited_at = models.DateTimeField(auto_now=True)


	def get_director_image_url(self):
		'''Return the director image URL or org chart image URL or default image'''
		if self.director_image and hasattr(self.director_image, 'url'):
			return self.director_image.url
		return static('faker/image.png')
	
	def get_org_chart_image_url(self):
		'''Return the org chart image URL or default image'''
		if self.org_chart_image and hasattr(self.org_chart_image, 'url'):
			return self.org_chart_image.url
		return static('faker/UESO ORG CHART.png')

	class Meta:
		indexes = [
			# Single-row table (typically only 1 record)
			# No complex queries needed
			models.Index(fields=['-edited_at'], name='aboutus_edit_idx'),
		]


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
