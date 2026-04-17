"""
File Upload Validators
Provides server-side validation for file uploads to enforce size limits.
Synced with settings.py: DATA_UPLOAD_MAX_MEMORY_SIZE and FILE_UPLOAD_MAX_MEMORY_SIZE (10MB)
"""

import os

from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_size(file):
    """
    Validate that uploaded file does not exceed maximum size limit.
    
    Args:
        file: UploadedFile instance
    
    Raises:
        ValidationError: If file size exceeds limit
    """
    # Get max file size from settings (default 10MB)
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10485760)  # 10MB in bytes
    
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f'File size ({file_size_mb:.2f}MB) exceeds maximum allowed size of {max_size_mb:.0f}MB.'
        )


def validate_image_size(image):
    """
    Validate that uploaded image does not exceed maximum size limit.
    
    Args:
        image: ImageField file instance
    
    Raises:
        ValidationError: If image size exceeds limit
    """
    validate_file_size(image)


def validate_valid_id_file(file):
    """Allow only image or PDF uploads for user valid IDs."""
    validate_file_size(file)

    allowed_extensions = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.heif'
    }
    extension = os.path.splitext(getattr(file, 'name', '') or '')[1].lower()
    content_type = (getattr(file, 'content_type', '') or '').lower()

    # Prefer MIME checks when available from request upload metadata.
    if content_type:
        if content_type == 'application/pdf' or content_type.startswith('image/'):
            return
        raise ValidationError('Valid ID must be an image or PDF file.')

    # Fallback for storage/file contexts without MIME metadata.
    if extension in allowed_extensions:
        return

    raise ValidationError('Valid ID must be an image or PDF file.')
