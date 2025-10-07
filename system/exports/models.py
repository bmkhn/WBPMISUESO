from django.db import models
from django.conf import settings

# Create your models here.

class ExportRequest(models.Model):
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
