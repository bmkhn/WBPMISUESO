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
    related_docs = models.ManyToManyField('RelatedDocument', blank=True, related_name='client_requests')
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


class RelatedDocument(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='client_requests/related_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Delete associated file from storage
        if self.file and self.file.storage and self.file.name and self.file.storage.exists(self.file.name):
            self.file.storage.delete(self.file.name)
        super().delete(*args, **kwargs)

########################################################################################################################


@receiver(post_delete, sender=ClientRequest)
def delete_orphan_related_docs(sender, instance, **kwargs):
    # Get all related docs before the m2m is cleared
    related_docs = list(instance.related_docs.all())
    for doc in related_docs:
        # If this was the only ClientRequest linked, delete the doc (and its file)
        if doc.client_requests.count() <= 1:
            doc.delete()