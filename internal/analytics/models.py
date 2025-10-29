# testingsite/models.py

import os
import io
import base64
import logging

from django.db import models
# Import Group and Permission for explicit related_name fields in User
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.core.files.base import ContentFile
# NOTE: Pillow (PIL) and pdf2image/poppler are required for ProjectDocument thumbnail generation.
# Make sure to install them: pip install Pillow pdf2image poppler-utils (or equivalent)
try:
    from PIL import Image
    from pdf2image import convert_from_path
    THUMBNAIL_LIBRARIES_AVAILABLE = True
except ImportError:
    THUMBNAIL_LIBRARIES_AVAILABLE = False
    logging.warning("Pillow or pdf2image/poppler not installed. Thumbnail generation for ProjectDocument will be skipped.")


# ==============================================================================
# Internal Models (e.g., Agenda, SDG)
# ==============================================================================

class College(models.Model):
    def delete(self, *args, **kwargs):
        # Delete associated logo file from storage
        if self.logo and self.logo.storage and self.logo.storage.exists(self.logo.name):
            self.logo.storage.delete(self.logo.name)
        super().delete(*args, **kwargs)

    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='colleges/logos/', blank=True, null=True)

    def __str__(self):
        return self.name

class Agenda(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    concerned_colleges = models.ManyToManyField(College, related_name='agendas')

    def __str__(self):
        return self.name

class SustainableDevelopmentGoal(models.Model):
    goal_number = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"SDG {self.goal_number}: {self.name}"

# ==============================================================================
# User Model (AbstractUser extended)
# ==============================================================================

class User(AbstractUser):
    def delete(self, *args, **kwargs):
        # Delete associated files from storage
        if self.profile_picture and self.profile_picture.storage and self.profile_picture.storage.exists(self.profile_picture.name):
            self.profile_picture.storage.delete(self.profile_picture.name)
        if self.valid_id and self.valid_id.storage and self.valid_id.storage.exists(self.valid_id.name):
            self.valid_id.storage.delete(self.valid_id.name)
        super().delete(*args, **kwargs)

    class Role(models.TextChoices):
        FACULTY = 'FACULTY', 'Faculty'
        IMPLEMENTER = 'IMPLEMENTER', 'Implementer'
        CLIENT = 'CLIENT', 'Client'
        UESO = 'UESO', 'UESO'
        COORDINATOR = 'COORDINATOR', 'College Coordinator'
        DEAN = 'DEAN', 'College Dean'
        PROGRAM_HEAD = 'PROGRAM_HEAD', 'Program Head'
        DIRECTOR = 'DIRECTOR', 'Director of Extension'
        VP = 'VP', 'Vice President'

    class Sex(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'

    class Campus(models.TextChoices):
        TINUIGIBAN = 'TINUIGIBAN', 'Tinuigiban'
        RIZAL = 'RIZAL', 'Rizal'
        NARRA = 'NARRA', 'Narra'
        QUEZON = 'QUEZON', 'Quezon'
        ARACELI = 'ARACELI', 'Araceli'
        BROOKES_POINT = 'BROOKES_POINT', "Brooke's Point"
        SAN_VICENTE = 'SAN_VICENTE', 'San Vicente'
        CUYO = 'CUYO', 'Cuyo'
        CORON = 'CORON', 'Coron'
        BALABAC = 'BALABAC', 'Balabac'
        ROXAS = 'ROXAS', 'Roxas'
        TAYTAY = 'TAYTAY', 'Taytay'
        EL_NIDO = 'EL_NIDO', 'El Nido'
        LINAPACAN = 'LINAPACAN', 'Linapacan'
        SAN_RAFAEL = 'SAN_RAFAEL', 'San Rafael'
        SOFRONIO_ESPANOLA = 'SOFRONIO_ESPANOLA', 'Sofronio Española'
        DUMARAN = 'DUMARAN', 'Dumaran'
        BATARAZA = 'BATARAZA', 'Bataraza'

    class PreferenceID(models.TextChoices):
        PASSPORT = 'PASSPORT', 'Passport'
        DRIVERS_LICENSE = 'DRIVERS_LICENSE', "Driver's License"
        UMID = 'UMID', 'UMID'
        SSS = 'SSS', 'SSS'
        GSIS = 'GSIS', 'GSIS'
        PRC = 'PRC', 'PRC'
        OTHERS = 'OTHERS', 'Others'

    # User fields
    given_name = models.CharField(max_length=150)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    last_name = models.CharField(max_length=150)
    suffix = models.CharField(max_length=10, blank=True, null=True)
    sex = models.CharField(max_length=6, choices=Sex.choices)
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=20)
    campus = models.CharField(max_length=30, choices=Campus.choices)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=Role.choices)
    degree = models.CharField(max_length=255, blank=True, null=True)
    expertise = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    is_expert = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='users/profile_pictures/', blank=True, null=True)
    preferred_id = models.CharField(max_length=50, blank=True, null=True, choices=PreferenceID.choices)
    valid_id = models.ImageField(upload_to='users/valid_ids/', blank=True, null=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False, null=False)
    
    # FIX for SystemCheckError: fields.E304 (Clashing reverse accessors)
    # These fields are inherited from AbstractUser, but must be redefined with 
    # unique related_names when using a custom user model in a non-default app.
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="testingsite_user_set", # <--- UNIQUE related_name
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="testingsite_user_permissions", # <--- UNIQUE related_name
        related_query_name="user",
    )

    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'given_name', 'last_name', 'sex', 'contact_no', 'role', 'valid_id']

    @property
    def profile_picture_or_initial(self):
        """
        Returns the profile picture URL if set, otherwise returns an SVG data URI with the user's first initial.
        """
        if self.profile_picture:
            try:
                return self.profile_picture.url
            except Exception:
                pass
        
        # Fallback to initial
        initial = (self.given_name or self.last_name or self.email or "?")[0].upper()
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><circle cx="20" cy="20" r="20" fill="#245F3E"/><text x="50%" y="55%" text-anchor="middle" fill="#fff" font-size="22" font-family="Arial" dy=".3em">{initial}</text></svg>'
        
        svg_b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f'data:image/svg+xml;base64,{svg_b64}'

    def get_full_name(self):
        mi = f"{self.middle_initial}. " if self.middle_initial else ""
        suffix = f" {self.suffix}" if self.suffix else ""
        return f"{self.given_name} {mi}{self.last_name}{suffix}"

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


# ==============================================================================
# Project Document Models and Helper
# ==============================================================================

def project_document_upload_to(instance, filename):
    # This helper function determines the upload path for ProjectDocument files.
    project_id = getattr(instance.project, 'id', 'unknown') # Use 'unknown' if project ID isn't set yet (e.g., during creation)
    if instance.document_type == 'PROPOSAL':
        return f"projects/{project_id}/proposals/{filename}"
    return f"projects/{project_id}/additional_documents/{filename}"


class ProjectDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('PROPOSAL', 'Proposal'),
        ('ADDITIONAL', 'Additional'),
    ]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=project_document_upload_to)
    document_type = models.CharField(max_length=12, choices=DOCUMENT_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=10, blank=True)
    thumbnail = models.ImageField(upload_to='project_thumbnails/', blank=True, null=True)


    def save(self, *args, **kwargs):
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = ext[1:] if ext else ''

            if THUMBNAIL_LIBRARIES_AVAILABLE:
                # Generate thumbnail for images and PDFs
                try:
                    if self.file_type in ['jpg', 'jpeg', 'png', 'gif']:
                        self.file.seek(0)  # Reset file pointer
                        img = Image.open(self.file)
                        img.thumbnail((300, 200))
                        thumb_io = io.BytesIO()
                        img.save(thumb_io, format='PNG')
                        self.thumbnail.save(f"thumb_{os.path.basename(self.file.name)}.png", ContentFile(thumb_io.getvalue()), save=False)
                    elif self.file_type == 'pdf':
                        # NOTE: pdf2image needs the file path, which means the file must be saved 
                        # to disk or accessible via a path before this is called.
                        if self.file.path:
                            pdf_path = self.file.path
                            pages = convert_from_path(pdf_path, first_page=1, last_page=1, size=(300, 200))
                            if pages:
                                thumb_io = io.BytesIO()
                                pages[0].save(thumb_io, format='PNG')
                                self.thumbnail.save(f"thumb_{os.path.basename(self.file.name)}.png", ContentFile(thumb_io.getvalue()), save=False)
                except Exception as e:
                    logging.error(f"Thumbnail generation failed for {self.file.name}: {e}")

        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        # Delete associated file from storage
        if self.file and self.file.storage and self.file.storage.exists(self.file.name):
            self.file.storage.delete(self.file.name)
        # Delete associated thumbnail from storage
        if self.thumbnail and self.thumbnail.storage and self.thumbnail.storage.exists(self.thumbnail.name):
            self.thumbnail.storage.delete(self.thumbnail.name)
        super().delete(*args, **kwargs)

    @property
    def name(self):
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
        if self.file:
            ext = os.path.splitext(self.file.name)[1]
            return ext[1:].lower() if ext else ""
        return ""

    def __str__(self):
        return f"{self.name} ({self.document_type})"

# ==============================================================================
# Project Models
# ==============================================================================

class Project(models.Model):
    def delete(self, *args, **kwargs):
        # Delete all related documents (which handles file deletion)
        for doc in self.documents.all():
            doc.delete() # Calls ProjectDocument's delete method to remove files
            
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
    STATUS_CHOICES = [
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("ON_HOLD", "On Hold"),
        ("CANCELLED", "Cancelled"),
    ]

    title = models.CharField(max_length=255)
    project_leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_projects')
    providers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='member_projects')
    agenda = models.ForeignKey(Agenda, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
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

    proposal_document = models.OneToOneField(ProjectDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposal_for_project')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_STARTED")

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def progress(self):
        # Placeholder: replace with real event logic
        # Calculates progress based on completed events vs. estimated total events
        return (self.events.filter(status='COMPLETED').count(), self.estimated_events or 0)

    @property
    def progress_display(self):
        done, total = self.progress
        if total and total > 0:
            percent = int((done / total) * 100)
            return f"{done}/{total} ({percent}%)"
        return "0/0 (0%)"

    def __str__(self):
        return self.title

# ==============================================================================
# Evaluation and Event Models
# ==============================================================================

class ProjectEvaluation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='evaluations')
    evaluated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='project_evaluations')
    created_at = models.DateField(auto_now_add=True)
    comment = models.TextField()
    rating = models.PositiveSmallIntegerField() 

    def __str__(self):
        return f"Evaluation of {self.project.title} by {self.evaluated_by.username if self.evaluated_by else 'Unknown'} on {self.created_at}"
    
def project_event_image_upload_to(instance, filename):
    project_id = getattr(instance.project, 'id', 'unknown')
    return f"projects/{project_id}/events/{filename}"

class ProjectEvent(models.Model):
    def delete(self, *args, **kwargs):
        # Delete associated image file from storage
        if self.image and self.image.storage and self.image.storage.exists(self.image.name):
            self.image.storage.delete(self.image.name)
        super().delete(*args, **kwargs)

    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    datetime = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_project_events')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_project_events')
    image = models.ImageField(upload_to=project_event_image_upload_to, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SCHEDULED")

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def __str__(self):
        return f"{self.title} ({self.project.title})"

# ==============================================================================
# Client Request Model
# ==============================================================================

class ClientRequest(models.Model):
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)
    primary_location = models.CharField(max_length=200)
    primary_beneficiary = models.CharField(max_length=200)
    summary = models.TextField()
    letter_of_intent = models.FileField(upload_to='client_requests/letters_of_intent/', blank=True, null=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_requests'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests'
    )
    review_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=[
        ('RECEIVED', 'Received'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ENDORSED', 'Endorsed'),
        ('DENIED', 'Denied'),
    ])

    def delete(self, *args, **kwargs):
        # Delete associated file from storage
        if self.letter_of_intent and self.letter_of_intent.storage and self.letter_of_intent.storage.exists(self.letter_of_intent.name):
            self.letter_of_intent.storage.delete(self.letter_of_intent.name)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_status_display(self):
        status_map = dict(self._meta.get_field('status').choices)
        return status_map.get(self.status, self.status.replace('_', ' ').title())