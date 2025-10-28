from django.db import models
from django.contrib.auth import get_user_model
from shared.projects.models import Project
from system.users.models import College

User = get_user_model()

class BudgetPool(models.Model):
    """Total available budget pool for each quarter/year"""
    quarter = models.CharField(max_length=10)  # e.g., "Q1-2024"
    fiscal_year = models.CharField(max_length=10)  # e.g., "2024"
    total_available = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Budget Pool {self.quarter} - ₱{self.total_available:,.2f}"
    
    class Meta:
        verbose_name_plural = "Budget Pools"
        unique_together = ['quarter', 'fiscal_year']

class BudgetCategory(models.Model):
    """Categories for budget allocation (e.g., Internal, External, Emergency)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Budget Categories"

class BudgetAllocation(models.Model):
    """Budget allocations for colleges/projects"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(BudgetCategory, on_delete=models.CASCADE)
    
    total_assigned = models.DecimalField(max_digits=15, decimal_places=2)
    total_remaining = models.DecimalField(max_digits=15, decimal_places=2)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    quarter = models.CharField(max_length=10)  # e.g., "Q1-2024"
    fiscal_year = models.CharField(max_length=10)  # e.g., "2024"
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='budget_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.college:
            return f"{self.college.name} - {self.category.name} ({self.quarter})"
        elif self.project:
            return f"{self.project.title} - {self.category.name} ({self.quarter})"
        return f"{self.category.name} ({self.quarter})"
    
    @property
    def utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.total_assigned > 0:
            return round((self.total_spent / self.total_assigned) * 100, 2)
        return 0
    
    @property
    def remaining_percentage(self):
        """Calculate remaining budget percentage"""
        if self.total_assigned > 0:
            return round((self.total_remaining / self.total_assigned) * 100, 2)
        return 0

class ExternalFunding(models.Model):
    """External funding sources and sponsors"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]
    
    sponsor_name = models.CharField(max_length=200)
    sponsor_contact = models.CharField(max_length=200, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    
    amount_offered = models.DecimalField(max_digits=15, decimal_places=2)
    amount_received = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    proposal_date = models.DateField()
    expected_completion = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.sponsor_name} - {self.project.title}"
    
    @property
    def completion_percentage(self):
        """Calculate funding completion percentage"""
        if self.amount_offered > 0:
            return round((self.amount_received / self.amount_offered) * 100, 2)
        return 0

class BudgetHistory(models.Model):
    """Track budget changes and transactions"""
    ACTION_CHOICES = [
        ('ALLOCATED', 'Budget Allocated'),
        ('SPENT', 'Budget Spent'),
        ('RETURNED', 'Budget Returned'),
        ('ADJUSTED', 'Budget Adjusted'),
        ('TRANSFERRED', 'Budget Transferred'),
    ]
    
    budget_allocation = models.ForeignKey(BudgetAllocation, on_delete=models.CASCADE, null=True, blank=True)
    external_funding = models.ForeignKey(ExternalFunding, on_delete=models.CASCADE, null=True, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action} - {self.amount} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name_plural = "Budget History"
        ordering = ['-timestamp']

class BudgetTemplate(models.Model):
    """Dynamic template configurations for different roles"""
    ROLE_CHOICES = [
        ('VP', 'Vice President'),
        ('DIRECTOR', 'Director'),
        ('UESO', 'UESO'),
        ('PROGRAM_HEAD', 'Program Head'),
        ('DEAN', 'Dean'),
        ('COORDINATOR', 'Coordinator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    template_name = models.CharField(max_length=100)
    template_path = models.CharField(max_length=200)
    
    # Template configuration
    show_overall_budget = models.BooleanField(default=True)
    show_historical_summary = models.BooleanField(default=True)
    show_detailed_view = models.BooleanField(default=True)
    show_external_funding = models.BooleanField(default=True)
    show_history = models.BooleanField(default=True)
    
    # Custom sections
    custom_sections = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_role_display()} - {self.template_name}"
