from django.db import models
from django.conf import settings
from rest_framework_api_key.models import APIKey

class SystemSetting(models.Model):
    """
    A key-value store for simple, site-wide settings.
    e.g., ('site_name', 'WBPMIS UESO'), ('maintenance_mode', 'False')
    """
    key = models.CharField(max_length=100, primary_key=True, unique=True, help_text="The unique identifier for the setting (e.g., 'site_name')")
    value = models.TextField(blank=True, help_text="The value of the setting.")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="A brief description of what this setting does.")

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ['key']

class APIConnection(models.Model):
    """
    Represents a persistent connection for a system or user accessing the API.
    This wrapper allows us to manage status (Pending/Active/Disconnected) 
    and keep the record even if the underlying key is revoked.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('DISCONNECTED', 'Disconnected'),
        ('REJECTED', 'Rejected'),
    ]

    name = models.CharField(max_length=255, help_text="Name of the system or user connecting.")
    description = models.TextField(blank=True, help_text="Reason for connection or system details.")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_connections')
    api_key = models.OneToOneField(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    #asc order
    class Meta:
        ordering = ['-created_at']