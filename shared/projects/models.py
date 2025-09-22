from django.db import models
from django.conf import settings



class SustainableDevelopmentGoal(models.Model):
	goal_number = models.PositiveSmallIntegerField(unique=True)
	name = models.CharField(max_length=255)

	def __str__(self):
		return f"SDG {self.goal_number}: {self.name}"

	@staticmethod
	def get_default_sdg_data():
		return [
			{'goal_number': 1, 'name': 'No Poverty'},
			{'goal_number': 2, 'name': 'Zero Hunger'},
			{'goal_number': 3, 'name': 'Good Health and Well-being'},
			{'goal_number': 4, 'name': 'Quality Education'},
			{'goal_number': 5, 'name': 'Gender Equality'},
			{'goal_number': 6, 'name': 'Clean Water and Sanitation'},
			{'goal_number': 7, 'name': 'Affordable and Clean Energy'},
			{'goal_number': 8, 'name': 'Decent Work and Economic Growth'},
			{'goal_number': 9, 'name': 'Industry, Innovation and Infrastructure'},
			{'goal_number': 10, 'name': 'Reduced Inequality'},
			{'goal_number': 11, 'name': 'Sustainable Cities and Communities'},
			{'goal_number': 12, 'name': 'Responsible Consumption and Production'},
			{'goal_number': 13, 'name': 'Climate Action'},
			{'goal_number': 14, 'name': 'Life Below Water'},
			{'goal_number': 15, 'name': 'Life on Land'},
			{'goal_number': 16, 'name': 'Peace, Justice and Strong Institutions'},
			{'goal_number': 17, 'name': 'Partnerships for the Goals'},
		]


def project_proposal_upload_to(instance, filename):
	# instance.id may not be set until after save, so use a placeholder if needed
	if instance.id:
		return f"projects/{instance.id}/proposals/{filename}"
	return f"projects/unknown/proposals/{filename}"

def project_additional_document_upload_to(instance, filename):
	# Try to get project id from related projects
	if hasattr(instance, 'projects') and instance.projects.exists():
		project_id = instance.projects.first().id
	else:
		project_id = 'unknown'
	return f"projects/{project_id}/additional_documents/{filename}"

class ProjectDocument(models.Model):
	file = models.FileField(upload_to=project_additional_document_upload_to)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	description = models.CharField(max_length=255, blank=True)
	def __str__(self):
		return self.file.name


class Project(models.Model):
	PROJECT_TYPE_CHOICES = [
		('NEEDS_BASED', 'Needs Based'),
		('RESEARCH_BASED', 'Research Based'),
	]
	LOGISTICS_TYPE_CHOICES = [
		('BOTH', 'Both'),
		('EXTERNAL', 'External'),
		('INTERNAL', 'Internal'),
	]

	title = models.CharField(max_length=255)
	project_leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_projects')
	providers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='member_projects')
	agenda = models.CharField(max_length=255)
	campus = models.CharField(max_length=255)
	project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES)
	sdgs = models.ManyToManyField(SustainableDevelopmentGoal, related_name='projects')
	estimated_events = models.PositiveIntegerField()
	estimated_trainees = models.PositiveIntegerField()
	primary_beneficiary = models.CharField(max_length=255)
	primary_location = models.CharField(max_length=255)
	logistics_type = models.CharField(max_length=10, choices=LOGISTICS_TYPE_CHOICES)
	internal_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	external_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	sponsor_name = models.CharField(max_length=255, blank=True)
	start_date = models.DateField()
	estimated_end_date = models.DateField()
	proposal_document = models.FileField(upload_to=project_proposal_upload_to)
	additional_documents = models.ManyToManyField(ProjectDocument, blank=True, related_name='projects')
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_projects')
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_projects')

	def __str__(self):
		return self.title
