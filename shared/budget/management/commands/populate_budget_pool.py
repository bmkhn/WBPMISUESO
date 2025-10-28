from django.core.management.base import BaseCommand
from shared.budget.models import BudgetPool
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate budget pool with initial data'

    def handle(self, *args, **options):
        # Create budget pools for current and next quarters
        current_year = 2025
        quarters = ['Q1-2025', 'Q2-2025', 'Q3-2025', 'Q4-2025']
        
        for quarter in quarters:
            budget_pool, created = BudgetPool.objects.get_or_create(
                quarter=quarter,
                fiscal_year=str(current_year),
                defaults={'total_available': Decimal('10000000')}  # ₱10M per quarter
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created budget pool for {quarter}: PHP {budget_pool.total_available:,.2f}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Budget pool for {quarter} already exists: PHP {budget_pool.total_available:,.2f}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated budget pools!')
        )
