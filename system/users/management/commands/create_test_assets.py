from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import faker 
from faker import Faker
from system.users.models import College, Campus
from shared.projects.models import SustainableDevelopmentGoal
from django.conf import settings
import os


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

CAMPUSES = [
    "Tinuigiban", "Rizal", "Narra", "Quezon", "Araceli", "Brooke's Point",
    "San Vicente", "Cuyo", "Coron", "Balabac", "Roxas", "Taytay",
    "El Nido", "Linapacan", "San Rafael", "Sofronio Española",
    "Dumaran", "Bataraza",
]

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
    help = "Populate test users, colleges, campuses, SDGs, agendas, and downloadables (idempotent)."

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # --- CAMPUSES ---
        if Campus.objects.exists():
            self.stdout.write(self.style.WARNING("Campuses already populated — skipping.\n"))
        else:
            self.stdout.write("Populating campuses...")
            campus_objs = {}
            for name in CAMPUSES:
                obj, _ = Campus.objects.get_or_create(name=name)
                campus_objs[name] = obj
            self.stdout.write(self.style.SUCCESS(f"Created {len(campus_objs)} campuses.\n"))

        campus_objs = {c.name: c for c in Campus.objects.all()}

        # --- COLLEGES ---
        if College.objects.exists():
            self.stdout.write(self.style.WARNING("Colleges already populated — skipping.\n"))
            college_objs_list = list(College.objects.all())
        else:
            self.stdout.write("Populating colleges (with logos)...")
            logo_dir = os.path.join(settings.MEDIA_ROOT, 'colleges', 'logos')
            os.makedirs(logo_dir, exist_ok=True)
            tinuigiban_campus = campus_objs.get("Tinuigiban")

            college_objs_list = []
            for name in COLLEGES:
                obj, _ = College.objects.get_or_create(name=name)
                campus_match = next((campus for cname, campus in campus_objs.items() if cname in name), None)
                obj.campus = campus_match or tinuigiban_campus
                obj.save(update_fields=["campus"])
                college_objs_list.append(obj)

                # Assign logo if exists
                logo_assigned = False
                for ext in [".png", ".jpg", ".jpeg", ".svg"]:
                    logo_path = os.path.join(logo_dir, f"{name}{ext}")
                    if os.path.exists(logo_path):
                        obj.logo = f"colleges/logos/{name}{ext}"
                        obj.save(update_fields=["logo"])
                        logo_assigned = True
                        break
                if not logo_assigned:
                    default_logo = os.path.join(logo_dir, "Default.png")
                    if os.path.exists(default_logo):
                        obj.logo = "colleges/logos/Default.png"
                        obj.save(update_fields=["logo"])
            self.stdout.write(self.style.SUCCESS(f"Created {len(college_objs_list)} colleges.\n"))

        # --- USERS ---
        self.stdout.write("Checking test users...")
        roles = [choice[0] for choice in User.Role.choices]
        default_password = "test1234"
        college_of_sciences = College.objects.filter(name="College of Sciences").first()
        created_users = 0
        for role in roles:
            email = f"{role.lower()}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=role.lower(),
                    email=email,
                    password=default_password,
                    given_name=role.capitalize(),
                    middle_initial="U",
                    last_name="Test",
                    sex=User.Sex.MALE,
                    contact_no="0999999999",
                    college=college_of_sciences if role in [
                        User.Role.COORDINATOR,
                        User.Role.DEAN,
                        User.Role.PROGRAM_HEAD,
                        User.Role.FACULTY
                    ] else None,
                    role=role,
                    is_confirmed=True,
                )
                created_users += 1
        if created_users:
            self.stdout.write(self.style.SUCCESS(f"Created {created_users} new test users.\n"))
        else:
            self.stdout.write(self.style.WARNING("All test users already exist — skipping.\n"))

        # --- SDGs ---
        if SustainableDevelopmentGoal.objects.exists():
            self.stdout.write(self.style.WARNING("SDGs already populated — skipping.\n"))
        else:
            for sdg in SDG_DATA:
                SustainableDevelopmentGoal.objects.get_or_create(
                    goal_number=sdg["goal_number"],
                    defaults={"name": sdg["name"]}
                )
            self.stdout.write(self.style.SUCCESS(f"Created {len(SDG_DATA)} SDGs.\n"))

        # --- AGENDAS ---
        from internal.agenda.models import Agenda
        if Agenda.objects.exists():
            self.stdout.write(self.style.WARNING("Agendas already populated — skipping.\n"))
        else:
            self.stdout.write("Populating agendas with concerned colleges...")

            def get_colleges(names):
                abbr = {
                    'CBA': 'College of Business and Accountancy',
                    'CAH': 'College of Arts and Humanities',
                    'CS': 'College of Sciences',
                    'CHTM': 'College of Hospitality Management and Tourism',
                    'CNHS': 'College of Nursing and Health Sciences',
                    'CEAT': 'College of Engineering',
                    'CCJE': 'College of Criminal Justice Education',
                    'CTE': 'College of Teacher Education',
                    'Graduate School': 'Graduate School',
                    'School of Medicine': 'School of Medicine',
                    'School of Law': 'School of Law',
                }
                results = []
                for n in names:
                    if n == "External Campus":
                        results.extend([c for c in College.objects.all() if c.campus and c.campus.name != "Tinuigiban"])
                    else:
                        full = abbr.get(n, n)
                        col = College.objects.filter(name=full).first()
                        if col:
                            results.append(col)
                return list(set(results))

            director = User.objects.filter(role=User.Role.DIRECTOR).first()
            agenda_samples = [
                {
                    'name': 'Economics, Entrepreneurship, and Livelihood Enhancement',
                    'description': 'Programs to enhance livelihood, entrepreneurship, and economic sustainability.',
                    'colleges': ['CBA', 'External Campus', 'Graduate School']
                },
                {
                    'name': 'Environmental IEC and Culture Sensitivity',
                    'description': 'Initiatives promoting environmental awareness, culture sensitivity, and sustainable practices.',
                    'colleges': ['CAH', 'CS']
                },
                {
                    'name': 'Hospitality and Tourism Industry Enhancement',
                    'description': 'Programs supporting tourism development, service quality, and industry innovation.',
                    'colleges': ['CHTM', 'External Campus']
                },
                {
                    'name': 'Agriculture, Environmental Protection, Conservation and Resource Management',
                    'description': 'Projects focused on agricultural sustainability, environmental protection, and resource conservation.',
                    'colleges': ['CS', 'External Campus', 'Graduate School']
                },
                {
                    'name': 'Promotive and Preventive Health, Nutrition and Gender Sensitivity',
                    'description': 'Programs advancing health awareness, nutrition, gender equality, and preventive healthcare.',
                    'colleges': ['CNHS', 'External Campus', 'Graduate School', 'School of Medicine', 'CAH']
                },
                {
                    'name': 'Engineering, Architecture and Appropriate Technology',
                    'description': 'Research and projects applying engineering and architectural innovations for societal benefit.',
                    'colleges': ['CEAT', 'CS', 'External Campus']
                },
                {
                    'name': 'Public Safety and Security, Disaster Risk Management and Governance',
                    'description': 'Initiatives for safety, disaster preparedness, governance, and community resilience.',
                    'colleges': ['CCJE', 'Graduate School', 'CNHS', 'School of Law']
                },
                {
                    'name': 'Literacy and Livelihood Learning Systems',
                    'description': 'Programs fostering literacy, education, and sustainable livelihood development.',
                    'colleges': ['CTE', 'Graduate School', 'CAH', 'External Campus']
                },
                {
                    'name': 'Leadership Enhancement and Governance',
                    'description': 'Training and programs to strengthen leadership, governance, and public administration.',
                    'colleges': ['Graduate School', 'CAH', 'CBA', 'External Campus', 'School of Law']
                },
            ]

            for a in agenda_samples:
                agenda, _ = Agenda.objects.get_or_create(name=a["name"], defaults={"description": a["description"]})
                agenda.concerned_colleges.set(get_colleges(a["colleges"]))
                agenda.created_by = director
                agenda.save()
            self.stdout.write(self.style.SUCCESS(f"Created {len(agenda_samples)} agendas.\n"))

        # --- DOWNLOADABLES ---
        from shared.downloadables.models import Downloadable
        if Downloadable.objects.exists():
            self.stdout.write(self.style.WARNING("Downloadables already populated — skipping.\n"))
        else:
            self.stdout.write("Populating downloadables...")
            downloadables_dir = os.path.join(settings.MEDIA_ROOT, 'downloadables', 'files')
            os.makedirs(downloadables_dir, exist_ok=True)
            uploader = User.objects.filter(role=User.Role.UESO).first() or User.objects.filter(role=User.Role.DIRECTOR).first()
            data = [
                {'name': 'PSU ESO 001 – Needs Assessment Form.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 002 – Client Satisfaction Form (English Version).docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 002 – Client Sattisfaction Form (Filipino Version).docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 003 – Project Monitoring Report Template.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 004 – Training Evaluation Form.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 005 – Feedback Form.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 006 – Accomplishment Report.docx', 'is_submission_template': True, 'submission_type': 'final'},
                {'name': 'PSU ESO 007 – Attendance Form.docx', 'is_submission_template': True, 'submission_type': 'event'},
                {'name': 'PSU ESO 008 – Certificate of Appearance.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 008 – Certificate of Participation.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'PSU ESO 008 – Certificate of Recognition.docx', 'is_submission_template': True, 'submission_type': 'file'},
                {'name': 'UESO Brochure.docx', 'is_submission_template': False, 'submission_type': 'file'},
            ]
            for d in data:
                path = os.path.join(downloadables_dir, d['name'])
                if not os.path.exists(path):
                    with open(path, 'w') as f:
                        f.write(f"Placeholder for {d['name']}")
                Downloadable.objects.get_or_create(
                    file=f'downloadables/files/{d["name"]}',
                    defaults={
                        'available_for_non_users': not d['is_submission_template'],
                        'is_submission_template': d['is_submission_template'],
                        'submission_type': d['submission_type'],
                        'uploaded_by': uploader,
                        'status': 'published',
                        'file_type': 'docx',
                    },
                )
            self.stdout.write(self.style.SUCCESS("Downloadables created.\n"))


        # --- ANNOUNCEMENTS ---
        from shared.announcements.models import Announcement
        if Announcement.objects.exists():
            self.stdout.write(self.style.WARNING("Announcements already populated — skipping.\n"))
        else:
            self.stdout.write("Populating announcements...")
            announcer = User.objects.filter(role=User.Role.UESO).first() or User.objects.filter(role=User.Role.DIRECTOR).first()

        director_user = User.objects.filter(role=User.Role.DIRECTOR).first()
        

        fake = Faker()


        from django.utils import timezone
        number_of_announcements = 5
        for i in range(number_of_announcements):
            title = fake.sentence(nb_words=6)
            body = fake.paragraph(nb_sentences=5)

            # Generate a random aware datetime within this year
            naive_dt = fake.date_time_this_year()
            aware_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
            ann = Announcement.objects.create(
                title=title,
                body=body,
                is_scheduled=False,
                published_by=director_user,
                published_at=aware_dt,
            )
        self.stdout.write(self.style.SUCCESS(f"{number_of_announcements} announcements created.\n"))

        # --- ABOUT US ---
        from shared.about_us.models import AboutUs
        if AboutUs.objects.exists():
            self.stdout.write(self.style.WARNING("About Us already populated — skipping.\n"))
        else:
            self.stdout.write("Populating About Us...")
            AboutUs.objects.update_or_create(
                id=1,
                defaults={
                    'hero_text': "Welcome to the About Us section of our platform. Here, we share our mission, vision, and the values that drive us to make a positive impact in our community.",
                    'vision_text': "Vision Text",
                    'mission_text': "Mission Text",
                    'thrust_text': "Thrust Text",
                    'leadership_description': "Leadership Description",
                    'director_name': "Dr. Liezl F. Tangonan",
                    'edited_by': director_user,
                    'edited_at': timezone.now(),
                }
            )
            self.stdout.write(self.style.SUCCESS("About Us created.\n"))
        self.stdout.write(self.style.SUCCESS("✅ Data population completed safely (idempotent).\n"))
