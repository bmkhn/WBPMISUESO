from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Campus(models.Model):
    """
    New model to store Campuses in the database for CRUD.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Campuses"
        ordering = ['name']


class College(models.Model):
    name = models.CharField(max_length=255)
    # We CHANGE the 'campus' field from CharField to a ForeignKey
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True)
    logo = models.ImageField(upload_to='colleges/logos/', blank=True, null=True)

    def delete(self, *args, **kwargs):
        if self.logo and self.logo.storage and self.logo.storage.exists(self.logo.name):
            self.logo.storage.delete(self.logo.name)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class User(AbstractUser):
    def delete(self, *args, **kwargs):
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
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, blank=True, null=True)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, blank=True, null=True)
    role = models.CharField(max_length=50, choices=Role.choices)
    degree = models.CharField(max_length=255, blank=True, null=True)
    expertise = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    is_expert = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='users/profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
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
        initial = (self.given_name or self.last_name or self.email or "?")[0].upper()
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><circle cx="20" cy="20" r="20" fill="#245F3E"/><text x="50%" y="55%" text-anchor="middle" fill="#fff" font-size="22" font-family="Arial" dy=".3em">{initial}</text></svg>'
        import base64
        svg_b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f'data:image/svg+xml;base64,{svg_b64}'
    preferred_id = models.CharField(max_length=50, blank=True, null=True, choices=PreferenceID.choices)  # e.g., Passport, Driver's License
    valid_id = models.ImageField(upload_to='users/valid_ids/', blank=True, null=True)       # Required Logic will be backend
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_users')
    updated_at = models.DateTimeField(null=True, blank=True)
    is_confirmed = models.BooleanField(default=False, null=False)

    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'given_name', 'last_name', 'sex', 'contact_no', 'role', 'valid_id']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_full_name(self):
        mi = f"{self.middle_initial}. " if self.middle_initial else ""
        suffix = f" {self.suffix}" if self.suffix else ""
        return f"{self.given_name} {mi}{self.last_name}{suffix}"

    def save(self, *args, **kwargs):
        # Only set updated_at if this is an update (object already exists)
        if self.pk:
            from django.utils import timezone
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)


# User logging is now handled manually in views for specific actions only:
# - Registration (CREATE)
# - Password Change
# - Edit Bio or Profile Picture
# - Added by UESO/Director/VP (CREATE)
# - Edited by UESO/Director/VP (UPDATE)
# This prevents excessive logging of every user save operation