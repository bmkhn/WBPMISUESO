from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os

class Downloadable(models.Model):
    def delete(self, *args, **kwargs):
        # Delete associated file and thumbnail from storage
        storage = self.file.storage if self.file else None
        if self.file and storage and storage.exists(self.file.name):
            storage.delete(self.file.name)
        if self.thumbnail and self.thumbnail.storage and self.thumbnail.storage.exists(self.thumbnail.name):
            self.thumbnail.storage.delete(self.thumbnail.name)
        super().delete(*args, **kwargs)

    DOWNLOADABLES_STATUS_CHOICES = [
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    file = models.FileField(upload_to='downloadables/files/')
    thumbnail = models.ImageField(upload_to='downloadables/thumbnails/', blank=True, null=True)
    available_for_non_users = models.BooleanField(default=False, help_text="Available for non-logged-in users")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_downloadables')
    status = models.CharField(max_length=16, choices=DOWNLOADABLES_STATUS_CHOICES, default='published')
    file_type = models.CharField(max_length=20, blank=True)
    is_submission_template = models.BooleanField(default=False, help_text="Used as a template for user submissions")
    SUBMISSION_TYPE_CHOICES = [
        ('event', 'Event'),
        ('final', 'Final'),
        ('file', 'File'),
    ]
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE_CHOICES, default='file')

    class Meta:
        indexes = [
            # Primary listing: Published files (authenticated users)
            models.Index(fields=['status', '-uploaded_at'], name='dl_status_date_idx'),
            # Public access filtering (non-authenticated users)
            models.Index(fields=['status', 'available_for_non_users'], name='dl_public_idx'),
            # File type filtering
            models.Index(fields=['file_type', 'status'], name='dl_type_status_idx'),
            # Submission template filtering (heavily used in submission views)
            models.Index(fields=['is_submission_template', 'submission_type'], name='dl_template_type_idx'),
            # Uploader tracking
            models.Index(fields=['uploaded_by', '-uploaded_at'], name='dl_uploader_idx'),
            # File search (name-based)
            models.Index(fields=['status', 'file_type'], name='dl_browse_idx'),
        ]
        verbose_name = 'Downloadable'
        verbose_name_plural = 'Downloadables'
        ordering = ['-uploaded_at']

    @property
    def name(self):
        if self.file:
            base = os.path.basename(self.file.name)
            return os.path.splitext(base)[0]
        return ""

    @property
    def name_with_ext(self):
        if self.file:
            return os.path.basename(self.file.name)
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
        return f"{self.name} ({self.file_type})"

    def save(self, *args, **kwargs):
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            self.file_type = ext[1:] if ext else ''

            # Generate thumbnail for images and PDFs
            try:
                from PIL import Image
                from pdf2image import convert_from_path
                import io
                from django.core.files.base import ContentFile
                if self.file_type in ['jpg', 'jpeg', 'png', 'gif']:
                    self.file.seek(0)  # Reset file pointer
                    img = Image.open(self.file)
                    img.thumbnail((300, 200))
                    thumb_io = io.BytesIO()
                    img.save(thumb_io, format='PNG')
                    self.thumbnail.save(f"thumb_{os.path.basename(self.file.name)}.png", ContentFile(thumb_io.getvalue()), save=False)
                elif self.file_type == 'pdf':
                    pdf_path = self.file.path
                    pages = convert_from_path(pdf_path, first_page=1, last_page=1, size=(300, 200))
                    if pages:
                        thumb_io = io.BytesIO()
                        pages[0].save(thumb_io, format='PNG')
                        self.thumbnail.save(f"thumb_{os.path.basename(self.file.name)}.png", ContentFile(thumb_io.getvalue()), save=False)
            except Exception as e:
                import logging
                logging.error(f"Thumbnail generation failed for {self.file.name}: {e}")
        super().save(*args, **kwargs)


@receiver(post_save, sender=Downloadable)
def log_downloadable_action(sender, instance, created, **kwargs):
    from system.logs.models import LogEntry
	# Skip logging if this is being called from within a signal to avoid duplicates
    if hasattr(instance, '_skip_log'):
        return
    action = 'CREATE' if created else 'UPDATE'
    LogEntry.objects.create(
        user=instance.uploaded_by,
        action=action,
        model='Downloadable',
        object_id=instance.id,
        object_repr=str(instance),
        details=f"File Type: {instance.file_type}, Status: {instance.status}"
    )


@receiver(post_delete, sender=Downloadable)
def log_downloadable_delete(sender, instance, **kwargs):
    from system.logs.models import LogEntry
    LogEntry.objects.create(
        user=instance.uploaded_by,
        action='DELETE',
        model='Downloadable',
        object_id=instance.id,
        object_repr=str(instance),
    )