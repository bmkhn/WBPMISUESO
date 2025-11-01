import os
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from system.logs.models import LogEntry
from django.urls import reverse


########################################################################################################################


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
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='reviewed_requests')
    review_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    endorsed_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='endorsed_requests')
    endorsed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='updated_requests')
    status = models.CharField(max_length=50, choices=[
        ('RECEIVED', 'Received'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ENDORSED', 'Endorsed'),
        ('DENIED', 'Denied'),
    ])

    class Meta:
        indexes = [
            # Primary workflow: Status filtering (RECEIVED, UNDER_REVIEW, APPROVED, etc.)
            models.Index(fields=['status', '-submitted_at'], name='req_status_submit_idx'),
            # Submitter lookup (client viewing their requests)
            models.Index(fields=['submitted_by', '-submitted_at'], name='req_submitter_idx'),
            # Admin review queue (RECEIVED/UNDER_REVIEW priority)
            models.Index(fields=['status', 'reviewed_by'], name='req_review_queue_idx'),
            # Endorsement workflow
            models.Index(fields=['status', 'endorsed_at'], name='req_endorsed_idx'),
            # Date range filtering (submitted and updated)
            models.Index(fields=['submitted_at'], name='req_submitted_date_idx'),
            models.Index(fields=['updated_at', 'status'], name='req_updated_status_idx'),
            # Organization search
            models.Index(fields=['organization'], name='req_org_idx'),
        ]
        verbose_name = 'Client Request'
        verbose_name_plural = 'Client Requests'

    @property
    def name(self):
        """Return the file name (without extension) of the uploaded letter_of_intent."""
        if self.letter_of_intent and self.letter_of_intent.name:
            filename = os.path.basename(self.letter_of_intent.name)  # e.g. 'client_requests/letters_of_intent/sample.pdf' → 'sample.pdf'
            name_without_ext, _ = os.path.splitext(filename)          # 'sample'
            return name_without_ext
        return ""

    
    def __str__(self):
        return self.title

    def get_status_display(self):
        status_map = dict(self._meta.get_field('status').choices)
        return status_map.get(self.status, self.status.replace('_', ' ').title())


# Log creation and update actions for ClientRequest
@receiver(post_save, sender=ClientRequest)
def log_client_request_action(sender, instance, created, **kwargs):
    user = instance.updated_by or instance.submitted_by or None
    url = reverse('request_details_dispatcher', args=[instance.id])
    
    # Create better detail messages
    if created:
        details = f"New request from {instance.organization}"
    else:
        status_messages = {
            'PENDING': 'Request is pending review',
            'APPROVED': 'Your request has been approved',
            'REJECTED': 'Your request has been rejected',
            'ENDORSED': 'Your request has been endorsed',
            'DENIED': 'Your request has been denied',
        }
        details = status_messages.get(instance.status, f"Request Status: {instance.get_status_display()}")
    
    # Only log creation if created
    if created:
        LogEntry.objects.create(
            user=user,
            action='CREATE',
            model='ClientRequest',
            object_id=instance.id,
            object_repr=instance.title,
            details=details,
            url=url,
            is_notification=True
        )
    # Only log update if not created and updated_at is set and not equal to submitted_at
    elif instance.updated_at and instance.updated_at != instance.submitted_at:
        LogEntry.objects.create(
            user=user,
            action='UPDATE',
            model='ClientRequest',
            object_id=instance.id,
            object_repr=instance.title,
            details=details,
            url=url,
            is_notification=True
        )


class RequestUpdate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    request = models.ForeignKey('ClientRequest', on_delete=models.CASCADE)
    status = models.CharField(max_length=32)
    viewed = models.BooleanField(default=False)
    updated_at = models.DateTimeField()

    class Meta:
        unique_together = ('user', 'request', 'status')
        indexes = [
            # User update feed (sorted by date, limited to 10)
            models.Index(fields=['user', '-updated_at'], name='req_upd_user_date_idx'),
            # Unread updates check
            models.Index(fields=['user', 'request', 'viewed'], name='req_upd_unread_idx'),
        ]