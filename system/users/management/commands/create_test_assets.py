from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from django.conf import settings
import os
import random

from system.users.models import College, Campus
from shared.projects.models import SustainableDevelopmentGoal, ProjectType
from shared.downloadables.models import Downloadable




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


# Faker seed keeps demo data predictable across runs for recordings.
Faker.seed(2026)
random.seed(2026)
fake = Faker("en_PH")


# Keep quick-login credentials the same, but make on-screen names look realistic.
QUICK_LOGIN_PROFILES = {
    'VP': {'given_name': 'Maria', 'middle_initial': 'L', 'last_name': 'Alcantara', 'sex': 'FEMALE'},
    'DIRECTOR': {'given_name': 'Antonio', 'middle_initial': 'R', 'last_name': 'Sarmiento', 'sex': 'MALE'},
    'UESO': {'given_name': 'Liezl', 'middle_initial': 'F', 'last_name': 'Tangonan', 'sex': 'FEMALE'},
    'COORDINATOR': {'given_name': 'Paolo', 'middle_initial': 'M', 'last_name': 'Navarro', 'sex': 'MALE'},
    'DEAN': {'given_name': 'Clarissa', 'middle_initial': 'D', 'last_name': 'Mendoza', 'sex': 'FEMALE'},
    'PROGRAM_HEAD': {'given_name': 'Ramon', 'middle_initial': 'T', 'last_name': 'Delos Santos', 'sex': 'MALE'},
    'FACULTY': {'given_name': 'Elaine', 'middle_initial': 'P', 'last_name': 'Garcia', 'sex': 'FEMALE'},
    'IMPLEMENTER': {'given_name': 'Joel', 'middle_initial': 'A', 'last_name': 'Rivera', 'sex': 'MALE'},
    'CLIENT': {'given_name': 'Patricia', 'middle_initial': 'C', 'last_name': 'Lopez', 'sex': 'FEMALE'},
}


class Command(BaseCommand):
    help = "Populate test users, colleges, campuses, SDGs, project types, agendas, client requests, and downloadables (idempotent)."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        from django.utils import timezone

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
        # Robust college logo copy logic: check staticfiles first, then static
        staticfiles_logo_dir = os.path.join(settings.BASE_DIR, 'staticfiles', 'colleges', 'logos')
        static_logo_dir = os.path.join(settings.BASE_DIR, 'static', 'colleges', 'logos')
        if os.path.exists(staticfiles_logo_dir) and os.listdir(staticfiles_logo_dir):
            logo_dir = staticfiles_logo_dir
        else:
            logo_dir = static_logo_dir
        tinuigiban_campus = campus_objs.get("Tinuigiban")
        media_logo_dir = os.path.join(settings.MEDIA_ROOT, 'colleges', 'logos')
        os.makedirs(media_logo_dir, exist_ok=True)
        for name in COLLEGES:
            for ext in [".png", ".jpg", ".jpeg", ".svg"]:
                src_logo_path = os.path.join(logo_dir, f"{name}{ext}")
                dest_logo_path = os.path.join(media_logo_dir, f"{name}{ext}")
                if os.path.exists(src_logo_path):
                    import shutil
                    shutil.copy2(src_logo_path, dest_logo_path)
        # Default logo
        default_logo_src = os.path.join(logo_dir, "Default.png")
        default_logo_dest = os.path.join(media_logo_dir, "Default.png")
        if os.path.exists(default_logo_src):
            import shutil
            shutil.copy2(default_logo_src, default_logo_dest)

        college_objs_list = []
        for name in COLLEGES:
            obj, _ = College.objects.get_or_create(name=name)
            campus_match = next((campus for cname, campus in campus_objs.items() if cname in name), None)
            obj.campus = campus_match or tinuigiban_campus
            obj.save(update_fields=["campus"])
            college_objs_list.append(obj)

            # Assign logo if exists in static
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
        updated_users = 0
        for role in roles:
            email = f"{role.lower()}@example.com"
            profile = QUICK_LOGIN_PROFILES.get(role, {
                'given_name': role.replace('_', ' ').title().split(' ')[0],
                'middle_initial': 'A',
                'last_name': 'Santos',
                'sex': 'MALE',
            })
            assigned_college = college_of_sciences if role in [
                User.Role.COORDINATOR,
                User.Role.DEAN,
                User.Role.PROGRAM_HEAD,
                User.Role.FACULTY,
            ] else None

            user = User.objects.filter(email=email).first()
            if not user:
                User.objects.create_user(
                    username=role.lower(),
                    email=email,
                    password=default_password,
                    given_name=profile['given_name'],
                    middle_initial=profile['middle_initial'],
                    last_name=profile['last_name'],
                    sex=User.Sex.FEMALE if profile['sex'] == 'FEMALE' else User.Sex.MALE,
                    contact_no="0999999999",
                    college=assigned_college,
                    role=role,
                    is_confirmed=True,
                )
                created_users += 1
                continue

            changed = False
            target_sex = User.Sex.FEMALE if profile['sex'] == 'FEMALE' else User.Sex.MALE
            target_values = {
                'username': role.lower(),
                'given_name': profile['given_name'],
                'middle_initial': profile['middle_initial'],
                'last_name': profile['last_name'],
                'sex': target_sex,
                'contact_no': '0999999999',
                'college': assigned_college,
                'role': role,
                'is_confirmed': True,
            }
            for field_name, value in target_values.items():
                if getattr(user, field_name) != value:
                    setattr(user, field_name, value)
                    changed = True

            # Keep quick-login credentials stable for demo recordings.
            if not user.check_password(default_password):
                user.set_password(default_password)
                changed = True

            if changed:
                user.save()
                updated_users += 1

        if created_users or updated_users:
            self.stdout.write(self.style.SUCCESS(
                f"Quick-login users ready: {created_users} created, {updated_users} updated (credentials preserved).\n"
            ))
        else:
            self.stdout.write(self.style.WARNING("Quick-login users already up to date — skipping.\n"))

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

        # --- PROJECT TYPES (NEW) ---
        if ProjectType.objects.exists():
            self.stdout.write(self.style.WARNING("Project Types already populated — skipping.\n"))
        else:
            self.stdout.write("Populating Project Types...")
            project_types = ["Needs Based", "Research Based"]
            for pt_name in project_types:
                ProjectType.objects.get_or_create(name=pt_name)
            self.stdout.write(self.style.SUCCESS(f"Created {len(project_types)} project types.\n"))

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


        # --- ANNOUNCEMENTS ---
        from shared.announcements.models import Announcement
        director_user = User.objects.filter(role=User.Role.DIRECTOR).first()

        if Announcement.objects.exists():
            self.stdout.write(self.style.WARNING("Announcements already populated — skipping.\n"))
        else:
            self.stdout.write("Populating announcements...")
            announcement_titles = [
                "Call for Extension Project Proposals for AY 2026",
                "Submission Timeline for Midyear Accomplishment Reports",
                "Orientation on Monitoring and Evaluation Tools",
                "Capacity Building Workshop for Community Partners",
                "Guidelines on Documentation and Evidence Upload",
            ]
            number_of_announcements = len(announcement_titles)
            for i, title in enumerate(announcement_titles):
                body = (
                    f"{title}\n\n"
                    f"{fake.paragraph(nb_sentences=3)}\n\n"
                    "For details, please coordinate with the University Extension Services Office."
                )

                # Generate a random aware datetime within this year
                naive_dt = fake.date_time_this_year()
                aware_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
                Announcement.objects.create(
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

        # --- CLIENT REQUESTS ---
        from shared.request.models import ClientRequest

        self.stdout.write("Seeding client requests...")

        # Keep a predictable LOI file for seeded requests.
        placeholder_rel_path = "client_requests/letters_of_intent/Placeholder.pdf"
        placeholder_src = os.path.join(settings.BASE_DIR, "static", "faker", "Placeholder.pdf")
        placeholder_dest_dir = os.path.join(settings.MEDIA_ROOT, "client_requests", "letters_of_intent")
        placeholder_available = False

        if os.path.exists(placeholder_src):
            os.makedirs(placeholder_dest_dir, exist_ok=True)
            placeholder_dest = os.path.join(placeholder_dest_dir, "Placeholder.pdf")
            if not os.path.exists(placeholder_dest):
                import shutil
                shutil.copy2(placeholder_src, placeholder_dest)
            placeholder_available = True
        else:
            self.stdout.write(self.style.WARNING(
                "Placeholder.pdf not found in static/faker; seeded requests will have no LOI file."
            ))

        request_statuses = [choice[0] for choice in ClientRequest._meta.get_field("status").choices]
        admin_reviewers = list(
            User.objects.filter(
                role__in=[User.Role.UESO, User.Role.DIRECTOR, User.Role.VP],
                is_confirmed=True,
                is_active=True,
            )
        )

        test_client_user = User.objects.filter(email="client@example.com", role=User.Role.CLIENT).first()
        other_client_users = list(
            User.objects.filter(role=User.Role.CLIENT, is_confirmed=True, is_active=True)
            .exclude(id=test_client_user.id if test_client_user else None)
            .order_by("id")
        )

        request_locations = [
            "Puerto Princesa City",
            "Narra",
            "Roxas",
            "Brooke's Point",
            "Taytay",
            "Coron",
        ]
        request_beneficiaries = [
            "Barangay youth leaders",
            "Women's association",
            "Farmers' cooperative",
            "Public school teachers",
            "MSME owners",
            "Fisherfolk community",
        ]

        test_client_topics = [
            "Digital literacy and basic computer operations",
            "Community entrepreneurship and microfinance coaching",
            "Disaster preparedness and barangay response planning",
            "Sustainable tourism and local product promotion",
            "Youth leadership and civic engagement training",
        ]
        other_client_topics = [
            "Financial bookkeeping support for community groups",
            "ICT upskilling for local government staff",
            "Public health awareness and preventive care campaign",
            "Coastal resource protection and biodiversity orientation",
            "Livelihood enhancement through food processing",
        ]

        def _aware(dt):
            if timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt.astimezone(timezone.get_current_timezone())

        def _build_request_defaults(client_user, topic, seed_index):
            status = random.choice(request_statuses)
            reviewer = random.choice(admin_reviewers) if admin_reviewers else None
            submitted_time = _aware(fake.date_time_between(start_date="-180d", end_date="-45d"))
            updated_time = _aware(fake.date_time_between(start_date="-30d", end_date="now"))

            defaults = {
                "organization": client_user.company or fake.company(),
                "primary_location": random.choice(request_locations),
                "primary_beneficiary": random.choice(request_beneficiaries),
                "summary": (
                    f"{topic}. "
                    f"Requested support includes {fake.sentence(nb_words=9)} "
                    f"and expected outcomes for community partners."
                ),
                "status": status,
                "reason": "",
            }

            if status in {"UNDER_REVIEW", "APPROVED", "REJECTED", "ENDORSED", "DENIED"}:
                defaults["reviewed_by"] = reviewer
                defaults["review_at"] = updated_time

            if status in {"ENDORSED", "DENIED"}:
                defaults["endorsed_by"] = reviewer
                defaults["endorsed_at"] = updated_time

            if status in {"REJECTED", "DENIED"}:
                defaults["reason"] = f"Additional requirements needed: {fake.sentence(nb_words=8)}"

            if status != "RECEIVED":
                defaults["updated_by"] = reviewer
                defaults["updated_at"] = updated_time

            return defaults, submitted_time

        def _upsert_request(client_user, title, topic, seed_index):
            defaults, submitted_time = _build_request_defaults(client_user, topic, seed_index)
            req, created = ClientRequest.objects.get_or_create(
                submitted_by=client_user,
                title=title,
                defaults=defaults,
            )

            updated = False
            if not created:
                changed_fields = []
                for field_name, value in defaults.items():
                    if getattr(req, field_name) != value:
                        setattr(req, field_name, value)
                        changed_fields.append(field_name)

                if changed_fields:
                    req.save(update_fields=changed_fields)
                    updated = True

            if req.submitted_at != submitted_time:
                ClientRequest.objects.filter(pk=req.pk).update(submitted_at=submitted_time)
                updated = True

            if placeholder_available and not req.letter_of_intent:
                req.letter_of_intent = placeholder_rel_path
                req.save(update_fields=["letter_of_intent"])
                updated = True

            return created, updated

        created_requests = 0
        updated_requests = 0

        if test_client_user:
            for idx, topic in enumerate(test_client_topics, start=1):
                title = topic  # No prefix
                created, updated = _upsert_request(test_client_user, title, topic, idx)
                created_requests += int(created)
                updated_requests += int(updated)
        else:
            self.stdout.write(self.style.WARNING("Test client user not found; skipped 5 primary demo requests."))

        if other_client_users:
            for idx, topic in enumerate(other_client_topics, start=1):
                target_client = other_client_users[(idx - 1) % len(other_client_users)]
                title = topic  # No prefix
                created, updated = _upsert_request(target_client, title, topic, idx)
                created_requests += int(created)
                updated_requests += int(updated)
        else:
            self.stdout.write(self.style.WARNING(
                "No additional confirmed client users found; created requests only for client@example.com."
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Client requests seeded: {created_requests} created, {updated_requests} updated."
        ))

        self.stdout.write(self.style.SUCCESS("✅ Data population completed safely (idempotent).\n"))


        # --- BUDGET ---
        from shared.budget.models import CollegeBudget
        from shared.budget.models import BudgetPool

        if BudgetPool.objects.exists():
            self.stdout.write(self.style.WARNING("Annual Budget already populated - skipping;.\n"))
        else:
            self.stdout.write("Populating annual budget...")
            # Create annual budget
            BudgetPool.objects.create(
                fiscal_year = "2026",
                total_available = 30000000,
                created_at = timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS("Annual Budget created.\n"))


        if CollegeBudget.objects.exists():
            self.stdout.write(self.style.WARNING("College Budget already populated — skipping.\n"))
        else:
            self.stdout.write("Populating college budget...")
            # Create a budget for each college
            for college in College.objects.all():
                CollegeBudget.objects.create(
                    college=college,
                    total_assigned=Decimal('700000.00'),  # Default budget amount
                    fiscal_year = "2026",
                    assigned_by=director_user,
                    created_at=timezone.now(),
                )
            self.stdout.write(self.style.SUCCESS("College Budget created.\n"))


        # --- DOWNLOADABLES ---
        # Add all files in static/downloadables/files as Downloadable objects
        downloadables_dir = os.path.join(settings.BASE_DIR, 'static', 'downloadables', 'files')
        media_downloadables_dir = os.path.join(settings.MEDIA_ROOT, 'downloadables', 'files')
        os.makedirs(media_downloadables_dir, exist_ok=True)
        import shutil
        if os.path.exists(downloadables_dir):
            for fname in os.listdir(downloadables_dir):
                src_path = os.path.join(downloadables_dir, fname)
                dest_path = os.path.join(media_downloadables_dir, fname)
                if not os.path.isfile(src_path):
                    continue
                # Copy file to media if not already present
                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_path)
                # Determine submission_type
                if fname.startswith('Activity Form Placeholder'):
                    submission_type = 'event'
                elif fname.startswith('Final Form Placeholder'):
                    submission_type = 'final'
                else:
                    submission_type = 'file'
                # Create Downloadable if not exists
                Downloadable.objects.get_or_create(
                    file=fname,
                    defaults={
                        'file': f'downloadables/files/{fname}',
                        'available_for_non_users': False,
                        'submission_type': submission_type,
                        'is_submission_template': True                    
                    }
                )
            self.stdout.write(self.style.SUCCESS(f"Downloadables created for all files in static/downloadables/files.\n"))
        