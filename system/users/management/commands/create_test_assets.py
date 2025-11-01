from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from system.users.models import College, Campus  # Make sure Campus is imported
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
    "School of Law",
    "School of Medicine",
]

# List of Campuses to populate the Campus model
CAMPUSES = [
    "Tinuigiban",
    "Rizal",
    "Narra",
    "Quezon",
    "Araceli",
    "Brooke's Point",
    "San Vicente",
    "Cuyo",
    "Coron",
    "Balabac",
    "Roxas",
    "Taytay",
    "El Nido",
    "Linapacan",
    "San Rafael",
    "Sofronio Española",
    "Dumaran",
    "Bataraza",
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
    help = "Populate test users, colleges, campuses, and SDGs for the system."

    def handle(self, *args, **kwargs):
        import random
        User = get_user_model()

        # --- Populate Campus Table ---
        created_campuses = 0
        campus_objs = {}  # Store campus objects for later
        for campus_name in CAMPUSES:
            campus_obj, created = Campus.objects.get_or_create(name=campus_name)
            if created:
                created_campuses += 1
            campus_objs[campus_name] = campus_obj  # Save for mapping
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created_campuses} new campuses.'))

        # --- FIX: Populate College Table (and update logos) ---
        self.stdout.write('Populating colleges and updating logos...')
        logo_dir = os.path.join(settings.MEDIA_ROOT, 'colleges', 'logos')
        college_objs_list = []  # To store created college objects for agendas
        created_colleges = 0
        
        # Get Tinuigiban campus to use as a default
        tinuigiban_campus = campus_objs.get("Tinuigiban")

        for name in COLLEGES:
            # Use get_or_create to make new colleges
            obj, created = College.objects.get_or_create(name=name)
            
            if created:
                created_colleges += 1
                # --- New Logic: Assign Campus ---
                found_campus = None
                for campus_name, campus_obj in campus_objs.items():
                    if campus_name in name: # e.g., "Roxas" is in "PSU Roxas"
                        found_campus = campus_obj
                        break
                
                # If no specific campus is found (e.g., "College of Sciences"), assign Tinuigiban
                if found_campus:
                    obj.campus = found_campus
                else:
                    obj.campus = tinuigiban_campus
                
                obj.save(update_fields=['campus'])
            
            college_objs_list.append(obj) # Add to list for agendas

            # --- Original Logo Logic (now updates new or existing colleges) ---
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
                    
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_colleges} new colleges and updated logos.'))

        # --- Create Test Users ---
        roles = [choice[0] for choice in User.Role.choices]
        default_password = "test1234"
        
        # Find College of Sciences
        college_of_sciences = next((c for c in college_objs_list if c.name == "College of Sciences"), None)
        
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
                    campus=campus, # This is now a Campus object
                    college=college,
                    role=role,
                    is_confirmed=True,
                    created_by=None,
                )
                self.stdout.write(self.style.SUCCESS(f"Created {role} user: {email} / {default_password}"))
            else:
                self.stdout.write(self.style.WARNING(f"{role} user already exists."))

        # --- Populate SDGs ---
        created_sdgs = 0
        for sdg in SDG_DATA:
            obj, created = SustainableDevelopmentGoal.objects.get_or_create(goal_number=sdg['goal_number'], defaults={'name': sdg['name']})
            if created:
                created_sdgs += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created_sdgs} new SDGs.'))

        # --- Create Sample Agendas ---
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
        
        if not college_objs_list:
            self.stdout.write(self.style.WARNING('No colleges found or created, skipping agenda creation.'))
        else:
            for agenda_data in agenda_samples:
                agenda_obj, created = Agenda.objects.get_or_create(
                    name=agenda_data['name'],
                    defaults={'description': agenda_data['description']}
                )
                if not created:
                    agenda_obj.description = agenda_data['description']
                    agenda_obj.save(update_fields=['description'])
                
                sample_size = min(len(college_objs_list), 3)
                selected_colleges = random.sample(college_objs_list, sample_size)
                agenda_obj.concerned_colleges.set(selected_colleges)
                agenda_obj.created_by = User.objects.filter(role=User.Role.DIRECTOR).first()
                agenda_obj.save()
            self.stdout.write(self.style.SUCCESS('Sample agendas created and associated with colleges.'))