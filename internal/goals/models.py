from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Goal(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('ON_HOLD', 'On Hold'),
    ]
    
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    target_value = models.IntegerField(help_text="Target number for this goal")
    current_value = models.IntegerField(default=0, help_text="Current progress value")
    unit = models.CharField(max_length=50, default="items", help_text="Unit of measurement (e.g., projects, students)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_goals')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_goals', null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)
    
    @property
    def is_overdue(self):
        return self.status == 'ACTIVE' and timezone.now().date() > self.target_date
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class GoalQualifier(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='qualifiers')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.goal.title} - {self.name}"
    
    class Meta:
        ordering = ['created_at']
