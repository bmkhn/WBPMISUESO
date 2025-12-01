from decimal import Decimal

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Backfill 'returned project balances' for already-completed projects
    that still have remaining budget but were completed before the
    automatic tracking was added.

    This will:
    - For each COMPLETED project with remaining_budget > 0:
      - Reduce the related CollegeBudget.total_assigned by the remaining amount
      - Increase the BudgetPool.total_available by the same amount
      - Create a BudgetHistory entry describing the return to UESO
    It is safe to run multiple times; projects already processed are skipped.
    """

    help = "Backfill returned project balances for completed projects with remaining budget."

    def handle(self, *args, **options):
        from shared.projects.models import Project
        from shared.budget.models import BudgetPool, CollegeBudget, BudgetHistory

        processed = 0
        skipped = 0

        completed_projects = Project.objects.filter(status="COMPLETED")

        for project in completed_projects:
            remaining = project.remaining_budget
            if not remaining or remaining <= 0:
                skipped += 1
                continue

            # Skip if we already logged a return for this project
            marker = f"Project: {project.title} (ID {project.id})"
            if BudgetHistory.objects.filter(description__icontains=marker).exists():
                skipped += 1
                continue

            fiscal_year = str(project.start_date.year) if project.start_date else None

            college_budget = None
            if getattr(project.project_leader, "college", None) and fiscal_year:
                college_budget = CollegeBudget.objects.filter(
                    college=project.project_leader.college,
                    fiscal_year=fiscal_year,
                    status="ACTIVE",
                ).first()

            # Adjust college allocation: remove remaining funds from the college "cut"
            if college_budget:
                original_total = college_budget.total_assigned or Decimal("0")
                if original_total >= remaining:
                    college_budget.total_assigned = original_total - remaining
                else:
                    college_budget.total_assigned = Decimal("0")
                college_budget.save(update_fields=["total_assigned", "updated_at"])

                BudgetHistory.objects.create(
                    college_budget=college_budget,
                    action="ADJUSTED",
                    amount=remaining,
                    description=(
                        "Returned unspent project budget to UESO for realignment. "
                        f"Project: {project.title} (ID {project.id})."
                    ),
                    user=None,
                )
            else:
                BudgetHistory.objects.create(
                    college_budget=None,
                    action="ADJUSTED",
                    amount=remaining,
                    description=(
                        "Returned unspent project budget to UESO for realignment (no CollegeBudget record). "
                        f"Project: {project.title} (ID {project.id})."
                    ),
                    user=None,
                )

            # Increase central pool for UESO
            if fiscal_year:
                pool, _ = BudgetPool.objects.get_or_create(
                    fiscal_year=fiscal_year,
                    defaults={"total_available": Decimal("0")},
                )
                pool.total_available = (pool.total_available or Decimal("0")) + remaining
                pool.save(update_fields=["total_available", "updated_at"])

            processed += 1

        self.stdout.write(
            f"Processed {processed} project(s); skipped {skipped} (no remaining budget or already logged)."
        )


