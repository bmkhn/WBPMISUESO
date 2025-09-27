from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from system.users.models import College
from shared.projects.models import SustainableDevelopmentGoal
import os
from django.conf import settings

# List of colleges
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

# List of SDGs (Sustainable Development Goals)
SDG_DATA = [
    {'goal_number': 1, 'name': 'No Poverty'},
    {'goal_number': 2, 'name': 'Zero Hunger'},
    {'goal_number': 3, 'name': 'Good Health and Well-being'},
    {'goal_number': 4, 'name': 'Quality Education'},
    {'goal_number': 5, 'name': 'Gender Equality'},
    {'goal_number': 6, 'name': 'Clean Water and Sanitation'},
    {'goal_number': 7, 'name': 'Affordable and Clean Energy'},
    {'goal_number': 8, 'name': 'Decent Work and Economic Growth'},
    {'goal_number': 9, 'name': 'Industry, Innovation and Infrastructure'},
    {'goal_number': 10, 'name': 'Reduced Inequality'},
    {'goal_number': 11, 'name': 'Sustainable Cities and Communities'},
    {'goal_number': 12, 'name': 'Responsible Consumption and Production'},
    {'goal_number': 13, 'name': 'Climate Action'},
    {'goal_number': 14, 'name': 'Life Below Water'},
    {'goal_number': 15, 'name': 'Life on Land'},
    {'goal_number': 16, 'name': 'Peace, Justice and Strong Institutions'},
    {'goal_number': 17, 'name': 'Partnerships for the Goals'},
]

class Command(BaseCommand):
    help = "Populate test users, colleges, and SDGs for the system."

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Create test users for each role
        roles = [choice[0] for choice in User.Role.choices]
        default_password = "test1234"
        for role in roles:
            email = f"{role.lower()}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=role.lower(),
                    email=email,
                    password=default_password,
                    given_name=role.capitalize(),
                    middle_initial="T",
                    last_name="User",
                    sex=User.Sex.MALE,
                    contact_no="0999999999",
                    campus=User.Campus.MAIN,
                    role=role,
                    is_confirmed=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Created {role} user: {email} / {default_password}"))
            else:
                self.stdout.write(self.style.WARNING(f"{role} user already exists."))

        # Populate College table (only create if missing, do not overwrite logos)
        logo_dir = os.path.join(settings.MEDIA_ROOT, 'colleges', 'logos')
        created = 0
        for name in COLLEGES:
            obj, was_created = College.objects.get_or_create(name=name)
            if was_created:
                logo_set = False
                for ext in ['.png', '.jpg', '.jpeg', '.svg']:
                    filename = f"{name}{ext}"
                    filepath = os.path.join(logo_dir, filename)
                    if os.path.exists(filepath):
                        obj.logo = f"colleges/logos/{filename}"
                        obj.save(update_fields=['logo'])
                        logo_set = True
                        break
                if not logo_set:
                    default_logo_path = os.path.join(logo_dir, 'Default.png')
                    if os.path.exists(default_logo_path):
                        obj.logo = "colleges/logos/Default.png"
                        obj.save(update_fields=['logo'])
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created} new colleges and set logos.'))

        # Populate SDGs (only create if missing)
        created_sdgs = 0
        for sdg in SDG_DATA:
            obj, created = SustainableDevelopmentGoal.objects.get_or_create(goal_number=sdg['goal_number'], defaults={'name': sdg['name']})
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created_sdgs} new SDGs populated.'))