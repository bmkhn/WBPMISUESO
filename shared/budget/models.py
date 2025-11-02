from django.db import models
from django.contrib.auth import get_user_model
from shared.projects.models import Project
from decimal import Decimal
from django.db.models import Sum

User = get_user_model()

# --- 1. Annual Budget Pool ---
class BudgetPool(models.Model):
    """Total available annual budget pool for the fiscal year"""
    fiscal_year = models.CharField(max_length=10, unique=True)
    total_available = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Annual Pool {self.fiscal_year} - ₱{self.total_available:,.2f}"
    
    class Meta:
        verbose_name_plural = "Annual Budget Pools"
        unique_together = ['fiscal_year']

# --- 2. CollegeBudget (The annual 'cut' - Simplified & Corrected) ---
class CollegeBudget(models.Model):
    """Annual Budget allocation (The 'cut') for a College."""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    # --- THIS IS THE FIX ---
    # The reference must be 'app_label.ModelName', not the full Python path.
    college = models.ForeignKey('users.College', on_delete=models.CASCADE)
    
    # This is the original 'cut' assigned to the college
    total_assigned = models.DecimalField(max_digits=15, decimal_places=2)
    
    fiscal_year = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='college_budget_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def _get_relevant_projects(self):
        """Helper to filter projects based on leader's college and fiscal year."""
        return Project.objects.filter(
            project_leader__college=self.college,
            start_date__year=self.fiscal_year 
        )
    
    @property
    def total_committed_to_projects(self):
        """Project Internal Funding: Sum of Project.internal_budget."""
        return self._get_relevant_projects().aggregate(Sum('internal_budget'))['internal_budget__sum'] or Decimal('0')
    
    @property
    def total_spent_by_projects(self):
        """Total Spent: Sum of Project.used_budget."""
        return self._get_relevant_projects().aggregate(Sum('used_budget'))['used_budget__sum'] or Decimal('0')
        
    @property
    def final_remaining(self):
        """Total Remaining (Cut minus Spent): total_assigned - total_spent_by_projects"""
        return self.total_assigned - self.total_spent_by_projects
    
    @property
    def uncommitted_remaining(self):
        """Uncommitted (Available for new projects): total_assigned - total_committed_to_projects"""
        return self.total_assigned - self.total_committed_to_projects

    class Meta:
        verbose_name = "College Budget Allocation"
        # A college should only have one annual budget entry per year
        unique_together = ['college', 'fiscal_year']
        indexes = [
            models.Index(fields=['college', 'status', 'fiscal_year'], name='colbud_col_stat_yr_idx'),
        ]

# --- 3. ExternalFunding (Retained as a separate list) ---
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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['project', 'status'], name='extfund_proj_stat_idx'),
            models.Index(fields=['status', '-proposal_date'], name='extfund_stat_date_idx'),
        ]

# --- 4. Budget History (Simplified FK) ---
class BudgetHistory(models.Model):
    """Track budget changes and transactions"""
    ACTION_CHOICES = [
        ('ALLOCATED', 'Budget Allocated'),
        ('SPENT', 'Budget Spent'),
        ('ADJUSTED', 'Budget Adjusted'),
    ]
    
    # Links to the root allocation object
    college_budget = models.ForeignKey(CollegeBudget, on_delete=models.SET_NULL, null=True, blank=True)
    external_funding = models.ForeignKey(ExternalFunding, on_delete=models.SET_NULL, null=True, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Budget History"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['college_budget', '-timestamp'], name='budhist_colbud_time_idx'),
            models.Index(fields=['external_funding', '-timestamp'], name='budhist_fund_time_idx'),
        ]