from django.db import models
from django.conf import settings
from rest_framework_api_key.models import APIKey

class SystemSetting(models.Model):
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
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('DISCONNECTED', 'Disconnected'),
        ('REJECTED', 'Rejected'),
    ]

    # Tiers for access control
    TIER_CHOICES = [
        ('TIER_1', 'Tier 1: Projects Read-Only'),
        ('TIER_2', 'Tier 2: Read All APIs'),
        ('TIER_3', 'Tier 3: Full Access'),
    ]

    name = models.CharField(max_length=255, help_text="Name of the system or user connecting.")
    description = models.TextField(blank=True, help_text="Reason for connection or system details.")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='api_connections')
    
    # Link to the secure (hashed) API Key
    api_key = models.OneToOneField(APIKey, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Store the visible string so the user can see it at all times
    full_api_key_string = models.CharField(max_length=255, blank=True, null=True, help_text="The visible API key string for the user.")

    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection.")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='TIER_1')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']