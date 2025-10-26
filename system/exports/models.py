from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Create your models here.

class ExportRequest(models.Model):
    querystring = models.TextField(blank=True, default='')
    EXPORT_TYPE_CHOICES = [
        ('MANAGE_USER', 'Manage User'),
        ('PROJECT', 'Project'),

    ]

    type = models.CharField(max_length=50, choices=EXPORT_TYPE_CHOICES)
    date_submitted = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='export_requests')
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ], default='PENDING')
    
    # Track who approved/rejected the export
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_exports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_type_display()} Export"

    def save(self, *args, **kwargs):
        # Only set updated_at if this is an update (object already exists)
        if self.pk:
            from django.utils import timezone
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

@receiver(post_save, sender=ExportRequest)
def log_export_request_action(sender, instance, created, **kwargs):
    from system.logs.models import LogEntry
    from django.urls import reverse
    
    action = 'CREATE' if created else 'UPDATE'
    
    # Determine the URL based on status
    # For APPROVED exports, link directly to the download
    # For REJECTED, no URL (empty string)
    # For PENDING, link to exports dashboard
    if instance.status == 'APPROVED':
        url = reverse('export_download', args=[instance.id])
    elif instance.status == 'REJECTED':
        url = ''  # No URL for rejected exports
    else:
        url = f"{reverse('exports')}#export-{instance.id}"
    
    # Determine the user for the log entry
    # For CREATE: use submitted_by
    # For UPDATE: use reviewed_by if available (approval/rejection), otherwise submitted_by
    if created:
        log_user = instance.submitted_by
        details = f"New export request for {instance.get_type_display()}"
    else:
        log_user = instance.reviewed_by if instance.reviewed_by else instance.submitted_by
        if instance.status == 'APPROVED':
            details = f"Your {instance.get_type_display()} export request has been approved"
        elif instance.status == 'REJECTED':
            details = f"Your {instance.get_type_display()} export request has been rejected"
        else:
            details = f"Export request status updated to {instance.status}"
    
    LogEntry.objects.create(
        user=log_user,
        action=action,
        model='ExportRequest',
        object_id=instance.id,
        object_repr=str(instance),
        details=details,
        url=url,
        is_notification=True
    )


@receiver(post_delete, sender=ExportRequest)
def log_export_request_delete(sender, instance, **kwargs):
    from system.logs.models import LogEntry
    LogEntry.objects.create(
        user=instance.submitted_by,
        action='DELETE',
        model='ExportRequest',
        object_id=instance.id,
        object_repr=str(instance),
        is_notification=True
    )


EXPORT_DIRECT_ROLES = [
    'VP',
    'DIRECTOR',
    'UESO',
]

EXPORT_REQUEST_ROLES = [
    'PROGRAM_HEAD',
    'DEAN',
    'COORDINATOR',
]

def can_export_direct(user):
    return hasattr(user, 'role') and user.role in EXPORT_DIRECT_ROLES

def must_request_export(user):
    return hasattr(user, 'role') and user.role in EXPORT_REQUEST_ROLES
