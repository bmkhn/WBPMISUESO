from django.core.management.base import BaseCommand
from shared.budget.models import (
    BudgetAllocation, BudgetCategory, ExternalFunding,
    BudgetHistory, BudgetTemplate, BudgetPool
)


class Command(BaseCommand):
    help = 'Clear all budget-related data (allocations, categories, external funding, history, templates, pools)'

    def handle(self, *args, **options):
        self.stdout.write('Clearing budget data...')

        counts = {
            'allocations': BudgetAllocation.objects.count(),
            'categories': BudgetCategory.objects.count(),
            'external': ExternalFunding.objects.count(),
            'history': BudgetHistory.objects.count(),
            'templates': BudgetTemplate.objects.count(),
            'pools': BudgetPool.objects.count(),
        }

        BudgetHistory.objects.all().delete()
        BudgetAllocation.objects.all().delete()
        ExternalFunding.objects.all().delete()
        BudgetCategory.objects.all().delete()
        BudgetTemplate.objects.all().delete()
        BudgetPool.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f"Deleted - Allocations: {counts['allocations']}, Categories: {counts['categories']}, "
            f"External: {counts['external']}, History: {counts['history']}, "
            f"Templates: {counts['templates']}, Pools: {counts['pools']}"
        ))


