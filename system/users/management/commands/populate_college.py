from django.core.management.base import BaseCommand
from system.users.models import College

COLLEGES = [
    "College of Arts and Humanities",
    "College of Business and Accountancy",
    "College of Criminal Justice Education",
    "College of Engineering",
    "College of Architecture",
    "College of Hospitality Management and Tourism",
    "College of Nursing and Health Sciences",
    "College of Sciences",
    "College of Teacher Education",

    "PSU PCAT Cuyo",
    "PSU Araceli",
    "PSU Balabac",
    "PSU Bataraza",
    "PSU Brooke’s Point",
    "PSU Coron",
    "PSU Dumaran",
    "PSU El Nido",
    "PSU Linapacan",
    "PSU Narra",
    "PSU Quezon",
    "PSU Rizal",
    "PSU Roxas",
    "PSU San Rafael",
    "PSU San Vicente",
    "PSU Sofronio Española",
    "PSU Taytay",

    "Graduate School",
    "Center for Transnational Education",
    "School of Law",
    "School of Medicine",
]

class Command(BaseCommand):
    help = 'Populate the College table with initial data.'

    def handle(self, *args, **options):
        created = 0
        for name in COLLEGES:
            obj, was_created = College.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created} colleges.'))
