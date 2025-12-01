from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from internal.agenda.models import Agenda
from shared.projects.models import Project, SustainableDevelopmentGoal


class Command(BaseCommand):
    help = "Create sample projects for testing, including one completed project with remaining budget."

    def handle(self, *args, **options):
        User = get_user_model()

        if Project.objects.filter(title__startswith="Sample Project").exists():
            self.stdout.write(self.style.WARNING("Sample projects already exist — skipping creation.\n"))
            return

        director = User.objects.filter(role=User.Role.DIRECTOR).first() or User.objects.first()
        faculty = (
            User.objects.filter(role__in=[User.Role.FACULTY, User.Role.IMPLEMENTER]).first()
            or director
        )

        if not director or not faculty:
            self.stdout.write(
                self.style.ERROR("Could not find suitable users (DIRECTOR / FACULTY) to own projects.")
            )
            return

        agenda = Agenda.objects.first()
        sdgs = list(SustainableDevelopmentGoal.objects.all()[:3])

        today = date.today()

        # 1) Ongoing needs-based project
        p1 = Project.objects.create(
            title="Sample Project - Community Literacy Program",
            project_leader=faculty,
            agenda=agenda,
            project_type="NEEDS_BASED",
            estimated_events=5,
            event_progress=2,
            estimated_trainees=150,
            total_trained_individuals=40,
            primary_beneficiary="Local community",
            primary_location="Main Campus Barangay",
            logistics_type="BOTH",
            internal_budget=Decimal("500000.00"),
            external_budget=Decimal("0.00"),
            sponsor_name="Internal Funds",
            start_date=today - timedelta(days=60),
            estimated_end_date=today + timedelta(days=30),
            used_budget=Decimal("150000.00"),
            status="IN_PROGRESS",
            has_final_submission=False,
            created_by=director,
            updated_by=director,
        )
        p1.providers.add(faculty)
        if sdgs:
            p1.sdgs.set(sdgs)

        # 2) Completed research-based project with remaining budget
        p2 = Project.objects.create(
            title="Sample Project - Completed Health Outreach",
            project_leader=faculty,
            agenda=agenda,
            project_type="RESEARCH_BASED",
            estimated_events=8,
            event_progress=8,
            estimated_trainees=300,
            total_trained_individuals=260,
            primary_beneficiary="Rural communities",
            primary_location="Remote Barangays",
            logistics_type="EXTERNAL",
            internal_budget=Decimal("200000.00"),
            external_budget=Decimal("100000.00"),
            sponsor_name="Health NGO",
            start_date=today - timedelta(days=365),
            estimated_end_date=today - timedelta(days=30),
            used_budget=Decimal("180000.00"),  # Not all 300,000 used → remaining budget
            status="COMPLETED",
            has_final_submission=True,
            created_by=director,
            updated_by=director,
        )
        p2.providers.add(faculty)
        if sdgs:
            p2.sdgs.set(sdgs[:2])

        # 3) Upcoming internal training project
        p3 = Project.objects.create(
            title="Sample Project - Upcoming Teacher Training",
            project_leader=faculty,
            agenda=agenda,
            project_type="NEEDS_BASED",
            estimated_events=3,
            event_progress=0,
            estimated_trainees=80,
            total_trained_individuals=0,
            primary_beneficiary="Public school teachers",
            primary_location="University Training Center",
            logistics_type="INTERNAL",
            internal_budget=Decimal("120000.00"),
            external_budget=Decimal("0.00"),
            sponsor_name="University",
            start_date=today + timedelta(days=30),
            estimated_end_date=today + timedelta(days=120),
            used_budget=Decimal("0.00"),
            status="NOT_STARTED",
            has_final_submission=False,
            created_by=director,
            updated_by=director,
        )
        p3.providers.add(faculty)
        if sdgs:
            p3.sdgs.set(sdgs[1:])

        # Ensure updated_at reflects creation time
        now = timezone.now()
        Project.objects.filter(id__in=[p1.id, p2.id, p3.id]).update(updated_at=now)

        # Avoid Unicode symbols that may not be supported in all Windows consoles
        self.stdout.write(
            self.style.SUCCESS(
                "Created 3 sample projects (including 1 completed project with remaining budget).\n"
            )
        )


