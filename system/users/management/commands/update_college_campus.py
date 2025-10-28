from django.core.management.base import BaseCommand
from system.users.models import College

class Command(BaseCommand):
    help = 'Update college campus assignments'

    def handle(self, *args, **options):
        # Tiniguiban Campus colleges
        tiniguiban_colleges = [
            "College of Arts and Humanities",
            "College of Business and Accountancy", 
            "College of Criminal Justice Education",
            "College of Engineering",
            "College of Architecture",
            "College of Hospitality Management and Tourism",
            "College of Nursing and Health Sciences",
            "College of Sciences",
            "College of Teacher Education",
            "Graduate School",
            "Center for Transnational Education",
            "School of Law",
            "School of Medicine",
        ]
        
        # External Campus colleges
        external_colleges = [
            "PSU PCAT Cuyo",
            "PSU Araceli",
            "PSU Balabac",
            "PSU Bataraza",
            "PSU Brooke's Point",
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
        ]
        
        # Update Tiniguiban colleges
        for college_name in tiniguiban_colleges:
            college, created = College.objects.get_or_create(
                name=college_name,
                defaults={'campus': 'TINIGUIBAN'}
            )
            if not created:
                college.campus = 'TINIGUIBAN'
                college.save()
            self.stdout.write(f"Updated {college_name} to Tiniguiban Campus")
        
        # Update External colleges
        for college_name in external_colleges:
            college, created = College.objects.get_or_create(
                name=college_name,
                defaults={'campus': 'EXTERNAL'}
            )
            if not created:
                college.campus = 'EXTERNAL'
                college.save()
            self.stdout.write(f"Updated {college_name} to External Campus")
        
        self.stdout.write(
            self.style.SUCCESS('Successfully updated college campus assignments!')
        )
