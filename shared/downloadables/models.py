from django.db import models
from django.conf import settings
import os

class Downloadable(models.Model):
    STATUS_CHOICES = [
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    file = models.FileField(upload_to='downloadables/files/')
    thumbnail = models.ImageField(upload_to='downloadables/thumbnails/', blank=True, null=True)
    available_for_non_users = models.BooleanField(default=False, help_text="Available for non-logged-in users")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_downloadables')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='published')
    file_type = models.CharField(max_length=20, blank=True)

    @property
    def name(self):
        if self.file:
            base = os.path.basename(self.file.name)
            return os.path.splitext(base)[0]
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