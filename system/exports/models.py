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

    def __str__(self):
        return f"{self.get_type_display()} export by {self.submitted_by} on {self.date_submitted:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        # Only set updated_at if this is an update (object already exists)
        if self.pk:
            from django.utils import timezone
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

@receiver(post_save, sender=ExportRequest)
def log_export_request_action(sender, instance, created, **kwargs):
    from system.logs.models import LogEntry
    action = 'CREATE' if created else 'UPDATE'
    LogEntry.objects.create(
        user=instance.submitted_by,
        action=action,
        model='ExportRequest',
        object_id=instance.id,
        object_repr=str(instance),
        details=f"Export Type: {instance.type}, Status: {instance.status}"
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
