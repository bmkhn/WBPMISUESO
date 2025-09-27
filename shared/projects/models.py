from django.db import models
from django.conf import settings



class SustainableDevelopmentGoal(models.Model):
	goal_number = models.PositiveSmallIntegerField(unique=True)
	name = models.CharField(max_length=255)

	def __str__(self):
		return f"SDG {self.goal_number}: {self.name}"

def project_document_upload_to(instance, filename):
	# instance.project may not be set until after save, so use a placeholder if needed
	project_id = getattr(instance.project, 'id', None)
	if instance.document_type == 'PROPOSAL':
		if project_id:
			return f"projects/{project_id}/proposals/{filename}"
		return f"projects/unknown/proposals/{filename}"
	else:
		if project_id:
			return f"projects/{project_id}/additional_documents/{filename}"
		return f"projects/unknown/additional_documents/{filename}"


class ProjectDocument(models.Model):
	def delete(self, *args, **kwargs):
		# Delete associated file from storage
		if self.file and self.file.storage and self.file.storage.exists(self.file.name):
			self.file.storage.delete(self.file.name)
		super().delete(*args, **kwargs)
		
	DOCUMENT_TYPE_CHOICES = [
		('PROPOSAL', 'Proposal'),
		('ADDITIONAL', 'Additional'),
	]
	project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='documents')
	file = models.FileField(upload_to=project_document_upload_to)
	document_type = models.CharField(max_length=12, choices=DOCUMENT_TYPE_CHOICES)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	description = models.CharField(max_length=255, blank=True)

	@property
	def name(self):
		import os
		if self.file:
			base = os.path.basename(self.file.name)
			return os.path.splitext(base)[0]
		return ""

	@property
	def size(self):
		if self.file and hasattr(self.file, 'size'):
			mb = self.file.size / (1024 * 1024)
			return f"{mb:.1f} MB"
		return "0.0 MB"

	@property
	def extension(self):
		import os
		if self.file:
			ext = os.path.splitext(self.file.name)[1]
			return ext[1:].lower() if ext else ""
		return ""

	def __str__(self):
		return f"{self.name} ({self.document_type})"



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
	internal_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
	external_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
	sponsor_name = models.CharField(max_length=255,  blank=True, null=True)
	start_date = models.DateField()
	estimated_end_date = models.DateField()

	proposal_document = models.OneToOneField('ProjectDocument', on_delete=models.SET_NULL, null=True, blank=True, related_name='proposal_for_project')
	additional_documents = models.ManyToManyField('ProjectDocument', blank=True, related_name='additional_for_projects')
	
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_projects')
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_projects')

	STATUS_CHOICES = [
		("NOT_STARTED", "Not Started"),
		("IN_PROGRESS", "In Progress"),
		("COMPLETED", "Completed"),
		("ON_HOLD", "On Hold"),
		("CANCELLED", "Cancelled"),
	]

	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_STARTED")

	def get_status_display(self):
		return dict(self.STATUS_CHOICES).get(self.status, self.status)

	@property
	def progress(self):
		# Placeholder: replace with real event logic
		# Example: done_events = self.events.filter(status='DONE').count()
		# total_events = self.events.count()
		# return (done_events, total_events)
		return (0, self.estimated_events or 0)

	@property
	def progress_display(self):
		done, total = self.progress
		if total:
			percent = int((done / total) * 100)
			return f"{done}/{total} ({percent}%)"
		return "0/0 (0%)"

	def __str__(self):
		return self.title
