from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shared.budget.models import (
    BudgetCategory, BudgetAllocation, ExternalFunding, 
    BudgetHistory, BudgetTemplate
)
from system.users.models import College
from shared.projects.models import Project
from decimal import Decimal
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate budget database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating budget sample data...')
        
        # Create Budget Categories
        categories = [
            {'name': 'Internal Operations', 'description': 'Internal university operations budget'},
            {'name': 'Research & Development', 'description': 'R&D projects and initiatives'},
            {'name': 'Community Outreach', 'description': 'Community service and outreach programs'},
            {'name': 'Infrastructure', 'description': 'Facilities and infrastructure improvements'},
            {'name': 'Emergency Fund', 'description': 'Emergency and contingency budget'},
        ]
        
        for cat_data in categories:
            category, created = BudgetCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create Budget Templates
        template_configs = [
            {
                'role': 'VP',
                'template_name': 'VP Budget Dashboard',
                'template_path': 'budget/vp_budget.html',
                'show_overall_budget': True,
                'show_historical_summary': True,
                'show_detailed_view': True,
                'show_external_funding': True,
                'show_history': True,
            },
            {
                'role': 'DIRECTOR',
                'template_name': 'Director Budget Dashboard',
                'template_path': 'budget/director_budget.html',
                'show_overall_budget': True,
                'show_historical_summary': True,
                'show_detailed_view': True,
                'show_external_funding': True,
                'show_history': True,
            },
        ]
        
        for template_data in template_configs:
            template, created = BudgetTemplate.objects.get_or_create(
                role=template_data['role'],
                defaults=template_data
            )
            if created:
                self.stdout.write(f'Created template: {template.template_name}')
        
        # Get existing data
        colleges = College.objects.all()[:5]  # Get first 5 colleges
        projects = Project.objects.all()[:10]  # Get first 10 projects
        categories = BudgetCategory.objects.all()
        users = User.objects.filter(role__in=['VP', 'DIRECTOR', 'UESO'])
        
        if not users.exists():
            self.stdout.write('No VP/DIRECTOR/UESO users found. Creating sample users...')
            # Create sample users if none exist
            vp_user = User.objects.create_user(
                username='vp_sample',
                email='vp@example.com',
                password='test1234',
                role='VP',
                first_name='VP',
                last_name='Sample'
            )
            director_user = User.objects.create_user(
                username='director_sample',
                email='director@example.com',
                password='test1234',
                role='DIRECTOR',
                first_name='Director',
                last_name='Sample'
            )
            users = [vp_user, director_user]
        
        # Create Budget Allocations
        current_year = date.today().year
        quarters = [f'Q{i}-{current_year}' for i in range(1, 5)]
        
        for i in range(20):  # Create 20 budget allocations
            college = random.choice(colleges) if colleges else None
            project = random.choice(projects) if projects else None
            category = random.choice(categories)
            quarter = random.choice(quarters)
            assigned_by = random.choice(users)
            
            total_assigned = Decimal(random.uniform(50000, 500000))
            total_spent = Decimal(random.uniform(0, total_assigned * 0.8))
            total_remaining = total_assigned - total_spent
            
            allocation = BudgetAllocation.objects.create(
                college=college,
                project=project,
                category=category,
                total_assigned=total_assigned,
                total_remaining=total_remaining,
                total_spent=total_spent,
                quarter=quarter,
                fiscal_year=str(current_year),
                assigned_by=assigned_by,
                status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'SUSPENDED'])  # Mostly active
            )
            
            # Create budget history entries
            BudgetHistory.objects.create(
                budget_allocation=allocation,
                action='ALLOCATED',
                amount=total_assigned,
                description=f'Initial budget allocation for {category.name}',
                user=assigned_by
            )
            
            if total_spent > 0:
                BudgetHistory.objects.create(
                    budget_allocation=allocation,
                    action='SPENT',
                    amount=total_spent,
                    description=f'Budget spent on {category.name} activities',
                    user=assigned_by
                )
        
        # Create External Funding
        sponsors = [
            'Department of Education',
            'National Science Foundation',
            'Local Government Unit',
            'Private Corporation',
            'International Organization',
            'Community Foundation',
            'Research Institute',
            'Technology Company',
        ]
        
        for i in range(15):  # Create 15 external funding records
            sponsor = random.choice(sponsors)
            project = random.choice(projects) if projects else None
            created_by = random.choice(users)
            
            amount_offered = Decimal(random.uniform(100000, 1000000))
            amount_received = Decimal(random.uniform(0, amount_offered))
            
            funding = ExternalFunding.objects.create(
                sponsor_name=sponsor,
                sponsor_contact=f'{sponsor} Contact',
                project=project,
                amount_offered=amount_offered,
                amount_received=amount_received,
                status=random.choice(['PENDING', 'APPROVED', 'APPROVED', 'COMPLETED']),
                proposal_date=date.today() - timedelta(days=random.randint(30, 365)),
                expected_completion=date.today() + timedelta(days=random.randint(30, 180)),
                created_by=created_by
            )
            
            # Create budget history for external funding
            BudgetHistory.objects.create(
                external_funding=funding,
                action='ALLOCATED',
                amount=amount_offered,
                description=f'External funding proposal from {sponsor}',
                user=created_by
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created budget sample data!')
        )
        self.stdout.write(f'- {BudgetCategory.objects.count()} budget categories')
        self.stdout.write(f'- {BudgetAllocation.objects.count()} budget allocations')
        self.stdout.write(f'- {ExternalFunding.objects.count()} external funding records')
        self.stdout.write(f'- {BudgetHistory.objects.count()} budget history entries')
        self.stdout.write(f'- {BudgetTemplate.objects.count()} budget templates')
