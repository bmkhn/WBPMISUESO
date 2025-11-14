import os
from django.db import models
from django.conf import settings
from internal.agenda.models import Agenda
from django.utils import timezone
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal
from django.urls import reverse
from system.logs.models import LogEntry
from system.utils.file_validators import validate_image_size
from django.templatetags.static import static


class SustainableDevelopmentGoal(models.Model):
	goal_number = models.PositiveSmallIntegerField(unique=True)
	name = models.CharField(max_length=255)

	class Meta:
		indexes = [
			models.Index(fields=['goal_number'], name='sdg_goal_number_idx'),
		]

	def __str__(self):
		return f"SDG {self.goal_number}: {self.name}"

####################################################################################################################################################################

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
	file_type = models.CharField(max_length=10, blank=True)
	thumbnail = models.ImageField(upload_to='project_thumbnails/', blank=True, null=True)

	def save(self, *args, **kwargs):
		if self.file:
			ext = os.path.splitext(self.file.name)[1].lower()
			self.file_type = ext[1:] if ext else ''

			# Generate thumbnail for images and PDFs
			try:
				from PIL import Image
				from pdf2image import convert_from_path
				import io
				from django.core.files.base import ContentFile
				if self.file_type in ['jpg', 'jpeg', 'png', 'gif']:
					self.file.seek(0)  # Reset file pointer
					img = Image.open(self.file)
					img.thumbnail((300, 200))
					thumb_io = io.BytesIO()
					img.save(thumb_io, format='PNG')
					self.thumbnail.save(f"thumb_{os.path.basename(self.file.name)}.png", ContentFile(thumb_io.getvalue()), save=False)
				elif self.file_type == 'pdf':
					pdf_path = self.file.path
					pages = convert_from_path(pdf_path, first_page=1, last_page=1, size=(300, 200))
					if pages:
						thumb_io = io.BytesIO()
						pages[0].save(thumb_io, format='PNG')
						self.thumbnail.save(f"thumb_{os.path.basename(self.file.name)}.png", ContentFile(thumb_io.getvalue()), save=False)
			except Exception as e:
				import logging
				logging.error(f"Thumbnail generation failed for {self.file.name}: {e}")
		super().save(*args, **kwargs)
		
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

	class Meta:
		indexes = [
			models.Index(fields=['project', 'document_type', 'uploaded_at'], name='project_docs_type_date_idx'),
			models.Index(fields=['project', 'uploaded_at'], name='project_docs_date_idx'),
			models.Index(fields=['document_type', 'uploaded_at'], name='docs_type_date_idx'),
		]

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

####################################################################################################################################################################


class Project(models.Model):
	def delete(self, *args, **kwargs):
		if self.proposal_document:
			self.proposal_document.delete()
		for doc in self.additional_documents.all():
			doc.delete()
		for doc in self.documents.all():
			doc.delete()
		super().delete(*args, **kwargs)

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
	agenda = models.ForeignKey(Agenda, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
	project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES)
	sdgs = models.ManyToManyField(SustainableDevelopmentGoal, related_name='projects')
	estimated_events = models.PositiveIntegerField()
	event_progress = models.PositiveIntegerField(default=0)
	estimated_trainees = models.PositiveIntegerField()
	total_trained_individuals = models.PositiveIntegerField(default=0)
	primary_beneficiary = models.CharField(max_length=255)
	primary_location = models.CharField(max_length=255)
	logistics_type = models.CharField(max_length=10, choices=LOGISTICS_TYPE_CHOICES)
	internal_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
	external_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True)
	sponsor_name = models.CharField(max_length=255,  blank=True, null=True)
	start_date = models.DateField()
	estimated_end_date = models.DateField()
	
	used_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Amount of the budget that has been spent.")

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
	has_final_submission = models.BooleanField(default=False, help_text="True when a final submission type has been approved")

	class Meta:
		indexes = [
			# CRITICAL: Scheduler queries run daily at midnight
			models.Index(fields=['status', 'start_date'], name='proj_status_start_idx'),
			models.Index(fields=['status', 'estimated_end_date', 'has_final_submission'], name='proj_completion_idx'),
			
			# Project listing and filtering
			models.Index(fields=['status', '-created_at'], name='proj_status_created_idx'),
			models.Index(fields=['-created_at'], name='proj_created_idx'),
			
			# Leader and provider lookups
			models.Index(fields=['project_leader', 'status'], name='proj_leader_status_idx'),
			
			# Agenda-based filtering
			models.Index(fields=['agenda', 'status'], name='proj_agenda_status_idx'),
		]

	def get_status_display(self):
		return dict(self.STATUS_CHOICES).get(self.status, self.status)

	@property
	def progress(self):
		if self.estimated_events:
			return (self.event_progress, self.estimated_events)

	@property
	def progress_display(self):
		done, total = self.progress
		if total:
			percent = int((done / total) * 100)
			return f"{done}/{total} ({percent}%)"
		return "0/0 (0%)"

	def __str__(self):
		return self.title

	def get_display_image_url(self):
		"""Return the latest non-placeholder event image or default project image"""
		# Try to get the latest event with an image that is not a placeholder
		latest_event = self.events.filter(placeholder=False, image__isnull=False).order_by('-datetime', '-created_at').first()
		if latest_event and latest_event.image:
			return latest_event.image.url
		return static('image.png')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._old_status = self.status

	def save(self, *args, **kwargs):
		# Store old status for signal
		if self.pk:
			try:
				old_instance = Project.objects.get(pk=self.pk)
				self._old_status = old_instance.status
			except Project.DoesNotExist:
				self._old_status = None
		super().save(*args, **kwargs)


# Log creation and update actions for Project
# NOTE: Imports moved to top for organization
@receiver(post_save, sender=Project)
def log_project_action(sender, instance, created, **kwargs):
	user = instance.updated_by or instance.created_by or None
	# project_profile view expects (request, pk) -> provide pk for reverse
	url = reverse('project_profile', args=[instance.pk])

	# Create better detail messages
	if created:
		details = f"A new project has been created"
	else:
		status_messages = {
			'NOT_STARTED': 'Project has not started yet',
			'IN_PROGRESS': 'Project is currently in progress',
			'COMPLETED': 'Project has been completed',
			'ON_HOLD': 'Project is on hold',
			'CANCELLED': 'Project has been cancelled',
		}
		details = status_messages.get(instance.status, f"Project Status: {instance.get_status_display()}")

	# Only log creation if created
	if created:
		LogEntry.objects.create(
			user=user,
			action='CREATE',
			model='Project',
			object_id=instance.id,
			object_repr=instance.title,
			details=details,
			url=url,
			is_notification=True
		)
	# Only log update if not created and status changed
	elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
		LogEntry.objects.create(
			user=user,
			action='UPDATE',
			model='Project',
			object_id=instance.id,
			object_repr=instance.title,
			details=details,
			url=url,
			is_notification=True
		)


@receiver(m2m_changed, sender=Project.providers.through)
def log_project_provider_added(sender, instance, action, pk_set, **kwargs):
	"""
	Notify users when they are added as providers to a project
	"""
	if action == 'post_add' and pk_set:
		from system.users.models import User
		from system.notifications.models import Notification
		url = reverse('project_profile', args=[instance.pk])
		actor = instance.updated_by or instance.created_by or None
		
		# Create a notification for each newly added provider
		for user_id in pk_set:
			try:
				added_user = User.objects.get(id=user_id)
				# Don't notify if the actor is the same as the added user
				if actor and added_user == actor:
					continue
				
				Notification.objects.create(
					recipient=added_user,
					actor=actor,
					action='UPDATE',
					model='Project',
					object_id=instance.id,
					object_repr=str(instance),
					details=f"You have been added as a provider to this project",
					url=url,
				)
			except User.DoesNotExist:
				pass


#############################################################################################################################################################################################################

def project_expense_upload_to(instance, filename):
    project_id = getattr(instance.project, 'id', None)
    if project_id:
        return f"projects/{project_id}/expenses/{filename}"
    return f"projects/unknown/expenses/{filename}"

class ProjectExpense(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=255)
    reason = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_incurred = models.DateField(default=timezone.now)
    receipt = models.FileField(upload_to=project_expense_upload_to, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} for {self.project.title} - ₱{self.amount}"

# --- SIGNAL HANDLERS for Project Budget Update ---

def update_project_used_budget(project_id):
    """
    Recalculates and updates the total used_budget for a given project.
    """
    # Import Project locally to avoid potential circular dependency issues
    from .models import Project 
    try:
        project = Project.objects.get(id=project_id)
        # Recalculate the sum of all related expenses. 
        total_used = project.expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        if project.used_budget != total_used:
            project.used_budget = total_used
            # Manually set updated_at and include it in update_fields to avoid infinite signal loops 
            # and ensure the auto_now field is updated.
            project.updated_at = timezone.now()
            project.save(update_fields=['used_budget', 'updated_at']) 
    except Project.DoesNotExist:
        pass

@receiver(post_save, sender=ProjectExpense)
def handle_project_expense_save(sender, instance, **kwargs):
    """Update Project.used_budget when an expense is created or updated."""
    update_project_used_budget(instance.project_id)

@receiver(post_delete, sender=ProjectExpense)
def handle_project_expense_delete(sender, instance, **kwargs):
    """Update Project.used_budget when an expense is deleted."""
    update_project_used_budget(instance.project.id)

#############################################################################################################################################################################################################


class ProjectEvaluation(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='evaluations')
	evaluated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='project_evaluations')
	created_at = models.DateField(auto_now_add=True)
	edited_at = models.DateTimeField(null=True, blank=True)
	comment = models.TextField()
	rating = models.PositiveSmallIntegerField() 

	class Meta:
		indexes = [
			# Project evaluations (most common query)
			models.Index(fields=['project', '-created_at'], name='proj_eval_proj_date_idx'),
			# User's evaluation history
			models.Index(fields=['evaluated_by', '-created_at'], name='proj_eval_user_idx'),
			# Rating-based filtering
			models.Index(fields=['project', 'rating'], name='proj_eval_rating_idx'),
		]

	def __str__(self):
		return f"Evaluation of {self.project.title} by {self.evaluated_by.username if self.evaluated_by else 'Unknown'} on {self.created_at}"
	

#############################################################################################################################################################################################################


def project_event_image_upload_to(instance, filename):
	project_id = getattr(instance.project, 'id', None)
	if project_id:
		return f"projects/{project_id}/events/{filename}"
	return f"projects/unknown/events/{filename}"

class ProjectEvent(models.Model):
	def delete(self, using=None, keep_parents=False):
		return super().delete(using=using, keep_parents=keep_parents)

	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='events')
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	datetime = models.DateTimeField(blank=True, null=True)
	location = models.CharField(max_length=255, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_project_events')
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_project_events')
	image = models.ImageField(upload_to=project_event_image_upload_to, blank=True, null=True, validators=[validate_image_size])
	placeholder = models.BooleanField(default=False)
	has_submission = models.BooleanField(default=False)

	STATUS_CHOICES = [
		("SCHEDULED", "Scheduled"),
		("ONGOING", "Ongoing"),
		("COMPLETED", "Completed"),
		("CANCELLED", "Cancelled"),
	]

	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")

	class Meta:
		indexes = [
			# CRITICAL: Scheduler query runs daily at midnight
			models.Index(fields=['status', 'datetime'], name='proj_evt_sched_date_idx'),
			
			# Project event timeline (latest_event property on Project model)
			models.Index(fields=['project', '-datetime', '-created_at'], name='proj_evt_timeline_idx'),
			
			# Event management and listing
			models.Index(fields=['project', 'status', '-datetime'], name='proj_evt_proj_status_idx'),
			models.Index(fields=['-datetime'], name='proj_evt_datetime_idx'),
			
			# Placeholder filtering (used in latest_event query)
			models.Index(fields=['placeholder', '-datetime'], name='proj_evt_placeholder_idx'),
		]

	def get_status_display(self):
		return dict(self.STATUS_CHOICES).get(self.status, self.status)

	def get_image_url(self):
		"""Return the event image URL or default image"""
		if self.image and hasattr(self.image, 'url'):
			return self.image.url
		return '/static/image.png'

	def __str__(self):
		return f"{self.title} ({self.project.title})"


#############################################################################################################################################################################################################


class ProjectExpenses(models.Model):
	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='legacy_expenses')
	reason = models.CharField(max_length=255)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	description = models.CharField(max_length=255)
	expense_date = models.DateField()
	receipt_img = models.ImageField(upload_to='project_expense_receipts/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_project_expenses')

	class Meta:
		indexes = [
			# Project expense tracking
			models.Index(fields=['project', '-expense_date'], name='proj_exp_proj_date_idx'),
			# Date-based filtering
			models.Index(fields=['-expense_date'], name='proj_exp_date_idx'),
		 ]

	def __str__(self):
		return f"Expense of {self.amount} for {self.project.title} on {self.expense_date}"


#############################################################################################################################################################################################################

class ProjectUpdate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=32)
    viewed = models.BooleanField(default=False)
    updated_at = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'project', 'submission', 'status')
        indexes = [
            # Update feed (unread notifications)
            models.Index(fields=['user', 'viewed', '-updated_at'], name='proj_upd_user_view_idx'),
            
            # Project-specific updates
            models.Index(fields=['project', '-updated_at'], name='proj_upd_proj_date_idx'),
        ]


# Signal handlers
# NOTE: Imports are at the top
@receiver(post_save, sender=Project)
def create_project_alerts(sender, instance, created, **kwargs):
    """Create project alerts when project status changes"""
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        # Notify project leader and providers about status changes
        users_to_notify = [instance.project_leader]
        if instance.providers.exists():
            users_to_notify.extend(instance.providers.all())
        
        for user in users_to_notify:
            if user:
                ProjectUpdate.objects.update_or_create(
                    user=user,
                    project=instance,
                    submission=None,  # No submission for project status changes
                    status=instance.status,
                    defaults={
                        'viewed': False,
                        'updated_at': timezone.now(),
                    }
                )