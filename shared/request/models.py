from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings


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

    def __str__(self):
        return self.title