from django.db import models

class AboutUs(models.Model):
	hero_text = models.TextField(blank=False, null=False, default="Hero Text")
	vision_text = models.TextField(blank=False, null=False, default="Vision Text")
	mission_text = models.TextField(blank=False, null=False, default="Mission Text")
	thrust_text = models.TextField(blank=False, null=False, default="Thrust Text")
	leadership_description = models.TextField(blank=False, null=False, default="Leadership Description")
	director_name = models.CharField(max_length=255, blank=True, null=True, default="Director Name")
	director_image = models.ImageField(upload_to='about_us/director/', blank=True, null=True, default=None)
	org_chart_image = models.ImageField(upload_to='about_us/org_chart/', blank=True, null=True, default=None)
	
	edited_by = models.CharField(max_length=255, blank=True, null=True)
	edited_at = models.DateTimeField(auto_now=True)
