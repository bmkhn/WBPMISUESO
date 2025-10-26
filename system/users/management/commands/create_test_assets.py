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
        import random
        User = get_user_model()

        # Populate College table (only create if missing, do not overwrite logos)
        logo_dir = os.path.join(settings.MEDIA_ROOT, 'colleges', 'logos')
        created = 0
        college_objs = []
        for name in COLLEGES:
            obj, was_created = College.objects.get_or_create(name=name)
            college_objs.append(obj)
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

        # Create test users for each role
        roles = [choice[0] for choice in User.Role.choices]
        default_password = "test1234"
        # Find College of Sciences and TINUIGIBAN campus
        college_of_sciences = next((c for c in college_objs if c.name == "College of Sciences"), None)
        tinuigiban_campus = User.Campus.TINUIGIBAN
        for role in roles:
            email = f"{role.lower()}@example.com"
            if not User.objects.filter(email=email).exists():
                if role in [User.Role.COORDINATOR, User.Role.DEAN, User.Role.PROGRAM_HEAD, User.Role.FACULTY]:
                    campus = tinuigiban_campus
                    college = college_of_sciences
                else:
                    campus = tinuigiban_campus
                    college = None
                user = User.objects.create_user(
                    username=role.lower(),
                    email=email,
                    password=default_password,
                    given_name=role.capitalize(),
                    middle_initial="T",
                    last_name="User",
                    sex=User.Sex.MALE,
                    contact_no="0999999999",
                    campus=campus,
                    college=college,
                    role=role,
                    is_confirmed=True,
                    created_by=None,
                )
                self.stdout.write(self.style.SUCCESS(f"Created {role} user: {email} / {default_password}"))
            else:
                self.stdout.write(self.style.WARNING(f"{role} user already exists."))

        # Populate SDGs (only create if missing)
        created_sdgs = 0
        for sdg in SDG_DATA:
            obj, created = SustainableDevelopmentGoal.objects.get_or_create(goal_number=sdg['goal_number'], defaults={'name': sdg['name']})
            if created:
                created_sdgs += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created_sdgs} new SDGs.'))

        # Create sample Agendas and associate with colleges
        from internal.agenda.models import Agenda
        agenda_samples = [
            {
                'name': 'Economics, Entrepreneurship, and Livelihood Enhancement',
                'description': 'Programs and activities aimed at improving economic opportunities, fostering entrepreneurship, and enhancing livelihood skills among communities.'
            },
            {
                'name': 'Environmental IEC and Culture Sensitivity',
                'description': 'Initiatives focused on environmental education, information dissemination, and promoting cultural sensitivity and awareness.'
            },
            {
                'name': 'Hospitality and Tourism Industry Enhancement',
                'description': 'Projects designed to strengthen the hospitality and tourism sectors through training, innovation, and community engagement.'
            },
        ]
        # Pick at least 3 colleges for each agenda
        for agenda_data in agenda_samples:
            agenda_obj, created = Agenda.objects.get_or_create(
                name=agenda_data['name'],
                defaults={'description': agenda_data['description']}
            )
            # Always update description in case it changed
            if not created:
                agenda_obj.description = agenda_data['description']
                agenda_obj.save(update_fields=['description'])
            # Associate with 3 random colleges
            selected_colleges = random.sample(college_objs, 3)
            agenda_obj.concerned_colleges.set(selected_colleges)
            agenda_obj.created_by = User.objects.filter(role=User.Role.DIRECTOR).first()
            agenda_obj.save()
        self.stdout.write(self.style.SUCCESS('Sample agendas created and associated with colleges.'))