from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    """
    Notification model to track user-specific notifications
    """
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('PUBLISH', 'Published'),
    ]
    
    # Who should see this notification
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # Who triggered the notification
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='triggered_notifications'
    )
    
    # What action was performed
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    
    # What type of object (Project, Submission, etc.)
    model = models.CharField(max_length=64)
    
    # ID of the object
    object_id = models.PositiveIntegerField()
    
    # String representation of the object
    object_repr = models.CharField(max_length=200)
    
    # Additional details about the action
    details = models.TextField(blank=True)
    
    # URL to view the object
    url = models.CharField(max_length=300, blank=True)
    
    # Notification status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # When the notification was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.actor} {self.get_action_display()} {self.model}: {self.object_repr}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def get_message(self):
        """Generate a human-readable notification message"""
        actor_name = self.actor.get_full_name() if self.actor else "Someone"
        action_past = {
            'CREATE': 'created',
            'UPDATE': 'updated',
            'DELETE': 'deleted',
            'PUBLISH': 'published',
        }.get(self.action, self.action.lower())
        
        return f"{actor_name} {action_past} {self.model.lower()}: {self.object_repr}"
