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
            # EXISTING: Recipient timeline (most common query)
            models.Index(fields=['recipient', '-created_at'], name='notif_recip_date_idx'),
            # EXISTING: Unread count (navbar/context processor - runs on EVERY page!)
            models.Index(fields=['recipient', 'is_read'], name='notif_recip_read_idx'),
            # NEW: Unread filtering with date sort (notification center)
            models.Index(fields=['recipient', 'is_read', '-created_at'], name='notif_unread_list_idx'),
            # NEW: Actor tracking (who triggered notifications)
            models.Index(fields=['actor', '-created_at'], name='notif_actor_idx'),
            # NEW: Model-based filtering
            models.Index(fields=['recipient', 'model'], name='notif_model_idx'),
            # NEW: Read status with timestamp (mark as read queries)
            models.Index(fields=['is_read', 'read_at'], name='notif_read_time_idx'),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
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
