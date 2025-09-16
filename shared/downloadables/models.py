from django.db import models
from django.conf import settings
import os

class Downloadable(models.Model):
    file = models.FileField(upload_to='downloadables/files/')

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
        return self.name