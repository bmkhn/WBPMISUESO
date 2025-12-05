from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from system.users.models import College, Campus
from shared.projects.models import Project, ProjectDocument, ProjectEvaluation, ProjectEvent, ProjectType, SustainableDevelopmentGoal
from internal.submissions.models import Submission
from shared.downloadables.models import Downloadable
from internal.agenda.models import Agenda
from django.utils import timezone
from datetime import timedelta
import random
from faker import Faker
import os
from django.conf import settings

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Generate test data for local dev, using actual media/static files (not URLs)"

    # Project Creation Helper
    def create_project(self, *, status, leader, providers, agendas, sdgs, director, file_templates, event_templates, final_templates, now, PLACEHOLDER_PDF_PATH, PLACEHOLDER_IMAGE_PATH):
        """
        Create a project with the given status and leader, using the same logic as before.
        """

        # Determine project details based on status
        if status == 'NOT_STARTED':
            start_date = now.date() + timedelta(days=random.randint(30, 90))
            end_date = start_date + timedelta(days=random.randint(180, 365))
            estimated_events = random.randint(3, 5)
            event_progress = 0
            estimated_trainees = random.randint(50, 200)
            total_trained_individuals = 0
            primary_beneficiary = random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials'])
            primary_location = random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido'])
        elif status == 'IN_PROGRESS':
            days_ago = random.randint(30, 120)
            start_date = (now - timedelta(days=days_ago)).date()
            end_date = start_date + timedelta(days=random.randint(180, 365))
            estimated_events = random.randint(4, 6)
            completed_events = random.randint(1, estimated_events - 1)
            event_progress = completed_events
            estimated_trainees = random.randint(50, 200)
            total_trained_individuals = random.randint(20, 100)
            primary_beneficiary = random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Barangay Officials'])
            primary_location = random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'San Vicente', "Brooke's Point"])
        elif status == 'COMPLETED':
            days_ago = random.randint(180, 365)
            start_date = (now - timedelta(days=days_ago)).date()
            duration = random.randint(90, 180)
            end_date = start_date + timedelta(days=duration)
            estimated_events = random.randint(3, 5)
            event_progress = estimated_events
            estimated_trainees = random.randint(100, 300)
            total_trained_individuals = random.randint(100, 300)
            primary_beneficiary = random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Indigenous Groups'])
            primary_location = random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'Narra', 'Quezon'])
        else:
            raise ValueError(f"Unknown status: {status}")

        logistics_type = random.choice(['INTERNAL', 'EXTERNAL', 'BOTH'])
        sponsor_name = ''
        internal_budget = 0
        external_budget = 0
        if logistics_type == 'EXTERNAL':
            sponsor_name = fake.company()
            external_budget = random.randint(50000, 150000)
        elif logistics_type == 'INTERNAL':
            internal_budget = random.randint(50000, 200000)
        elif logistics_type == 'BOTH':
            sponsor_name = fake.company()
            internal_budget = random.randint(50000, 150000)
            external_budget = random.randint(50000, 150000)

        project_type = random.choice(ProjectType.objects.all())

        # Create the project with the determined details
        project = Project.objects.create(
            title=f"{fake.catch_phrase()} - {random.choice(['Training Program', 'Workshop Series', 'Community Seminar', 'Extension Service', 'Skills Training', 'Community Workshop', 'Extension Program', 'Outreach Activity', 'Community Development', 'Skills Enhancement', 'Livelihood Program', 'Health Initiative'])}",
            project_leader=leader,
            agenda=random.choice(agendas),
            project_type=project_type,
            estimated_events=estimated_events,
            event_progress=event_progress,
            estimated_trainees=estimated_trainees,
            total_trained_individuals=total_trained_individuals,
            primary_beneficiary=primary_beneficiary,
            primary_location=primary_location,
            logistics_type=logistics_type,
            internal_budget=internal_budget,
            external_budget=external_budget,
            sponsor_name=sponsor_name,
            start_date=start_date,
            estimated_end_date=end_date,
            status=status,
            has_final_submission=(status == 'COMPLETED'),
            created_by=director,
            updated_by=director,
        )
        project.providers.set(providers)
        if status == 'COMPLETED':
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 5)))
        else:
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))

        # Proposal document
        proposal_doc = ProjectDocument.objects.create(
            project=project,
            document_type='PROPOSAL',
            description='Project Proposal Document'
        )
        proposal_doc.file.name = PLACEHOLDER_PDF_PATH
        proposal_doc.save()
        project.proposal_document = proposal_doc
        project.save(update_fields=['proposal_document'])

        # Additional documents
        if status == 'NOT_STARTED':
            additional_count = random.randint(1, 2)
        elif status == 'IN_PROGRESS':
            additional_count = random.randint(1, 3)
        else:
            additional_count = random.randint(2, 4)
        for doc_num in range(additional_count):
            add_doc = ProjectDocument.objects.create(
                project=project,
                document_type='ADDITIONAL',
                description=f'Additional Document {doc_num + 1}'
            )
            add_doc.file.name = PLACEHOLDER_PDF_PATH
            add_doc.save()
            project.additional_documents.add(add_doc)

        # Events and Submissions
        if status in ['IN_PROGRESS', 'COMPLETED']:
            if status == 'IN_PROGRESS':
                event_loop_count = estimated_events
                completed_events = event_progress
                duration = None
                start_date_for_events = start_date
            else:
                event_loop_count = estimated_events
                completed_events = estimated_events
                duration = end_date - start_date
                start_date_for_events = start_date
            for j in range(event_loop_count):
                if status == 'IN_PROGRESS':
                    days_offset = random.randint(0, (now.date() - start_date_for_events).days if (now.date() - start_date_for_events).days > 0 else 1)
                    event_date = now - timedelta(days=days_offset)
                    event_status = 'COMPLETED' if event_date.date() <= now.date() else 'SCHEDULED'
                else:
                    days_offset = random.randint(0, duration.days - 10 if duration and duration.days > 10 else 1)
                    event_date = timezone.make_aware(timezone.datetime.combine(start_date_for_events + timedelta(days=days_offset), timezone.datetime.min.time()))
                    event_status = 'COMPLETED'
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"{random.choice(['Training Session', 'Workshop', 'Seminar', 'Consultation', 'Field Visit', 'Technical Assistance', 'Monitoring Visit'])}",
                    description=f"A description of an activity for {project.title}",
                    datetime=event_date,
                    location=project.primary_location,
                    status=event_status,
                    has_submission=True,
                    placeholder=False,
                    created_by=leader,
                    updated_by=leader,
                )
                if (status == 'IN_PROGRESS' and j < completed_events and event_templates) or (status == 'COMPLETED' and event_templates):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    coordinator = User.objects.filter(
                        role=User.Role.COORDINATOR,
                        college=leader.college
                    ).first()
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(event_templates),
                        deadline=event_date + timedelta(days=7),
                        notes=f"Notes for {event.title}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(20, 80) if status == 'IN_PROGRESS' else random.randint(30, 60),
                        image_description=f"Photo from {event.title}" if status == 'IN_PROGRESS' else f"Documentation photo from {event.title}",
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,
                        reviewed_at=event_date + timedelta(days=random.randint(6, 8)) if status == 'IN_PROGRESS' else event_date + timedelta(days=random.randint(6, 7)),
                        authorized_by=director,
                        authorized_at=event_date + timedelta(days=random.randint(9, 10)) if status == 'IN_PROGRESS' else event_date + timedelta(days=random.randint(8, 10)),
                        updated_by=director,
                    )
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.image_event.name = PLACEHOLDER_IMAGE_PATH
                    submission.save()

        # File submissions
        if status in ['IN_PROGRESS', 'COMPLETED'] and file_templates:
            if status == 'IN_PROGRESS':
                num_file_submissions = random.randint(2, 3)
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                for k in range(num_file_submissions):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    deadline_date = start_date + timedelta(days=random.randint(30, (now - timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))).days if (now - timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))).days > 0 else 1))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    status_choices = ['SUBMITTED', 'FORWARDED', 'APPROVED']
                    status_val = random.choice(status_choices)
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Required documentation {k+1}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status=status_val,
                        reviewed_by=coordinator if coordinator and status_val != 'SUBMITTED' else (director if status_val != 'SUBMITTED' else None),
                        reviewed_at=deadline - timedelta(days=1) if status_val != 'SUBMITTED' else None,
                        authorized_by=director if status_val in ['FORWARDED', 'APPROVED'] else None,
                        authorized_at=deadline if status_val in ['FORWARDED', 'APPROVED'] else None,
                        updated_by=director,
                    )
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.save()
            elif status == 'COMPLETED':
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                for k in range(3):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    deadline_date = end_date - timedelta(days=random.randint(10, 30))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Notes {k+1}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,
                        reviewed_at=deadline,
                        authorized_by=director,
                        authorized_at=deadline + timedelta(days=1),
                        updated_by=director,
                    )
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.save()

        # Final submission for COMPLETED
        if status == 'COMPLETED' and final_templates:
            submitter = leader
            deadline_date = end_date + timedelta(days=7)
            deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
            submission = Submission.objects.create(
                project=project,
                downloadable=random.choice(final_templates),
                deadline=deadline,
                notes="Final Accomplishment Report",
                created_by=director,
                submitted_by=submitter,
                submitted_at=deadline - timedelta(days=2),
                for_product_production=random.choice([True, False]),
                for_research=random.choice([True, False]),
                for_extension=True,
                status='APPROVED',
                reviewed_by=director,
                reviewed_at=deadline,
                authorized_by=director,
                authorized_at=deadline,
                updated_by=director,
            )
            submission.file.name = PLACEHOLDER_PDF_PATH
            submission.save()

        return project

    # Projects Creation Helper for a Leader (Faculty U. Test)
    def create_projects_for_leader(self, leader, status, count, faculty_users, agendas, sdgs, director, file_templates, event_templates, final_templates, now, PLACEHOLDER_PDF_PATH, PLACEHOLDER_IMAGE_PATH, project_count):
        for _ in range(count):
            providers = [leader] + random.sample([u for u in faculty_users if u != leader], k=min(random.randint(1, 2), len(faculty_users)-1))
            project = self.create_project(
                status=status,
                leader=leader,
                providers=providers,
                agendas=agendas,
                sdgs=sdgs,
                director=director,
                file_templates=file_templates,
                event_templates=event_templates,
                final_templates=final_templates,
                now=now,
                PLACEHOLDER_PDF_PATH=PLACEHOLDER_PDF_PATH,
                PLACEHOLDER_IMAGE_PATH=PLACEHOLDER_IMAGE_PATH
            )
            project_count[0] += 1

    # Main Command Handler
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting Local asset generation...\n'))

        faculty_user_count = 25
        no_of_ns_projects = 5
        no_of_ip_projects = 5
        no_of_c_projects = 5

        no_of_ns_faculty_projects = 2
        no_of_ip_faculty_projects = 2
        no_of_c_faculty_projects = 2

        # Use static/faker/Placeholder.pdf and static/faker/image.png for all file/image fields
        PLACEHOLDER_PDF_PATH = "faker/Placeholder.pdf"
        PLACEHOLDER_IMAGE_PATH = "faker/image.png"

        # Fetch required related objects
        colleges = list(College.objects.all())
        agendas = list(Agenda.objects.all())
        sdgs = list(SustainableDevelopmentGoal.objects.all())
        downloadables = list(Downloadable.objects.all())

        # Validations
        if not colleges:
            self.stdout.write(self.style.ERROR('No colleges found. Run create_test_assets first.'))
            return
        if not agendas:
            self.stdout.write(self.style.ERROR('No agendas found. Run create_test_assets first.'))
            return
        if not downloadables:
            self.stdout.write(self.style.ERROR('No downloadables found. Run create_test_assets first.'))
            return
        director = User.objects.filter(role=User.Role.DIRECTOR).first()
        if not director:
            self.stdout.write(self.style.ERROR('No director found. Run create_test_assets first.'))
            return

        # Degree to expertise mapping for Faculty users
        degree_expertise_map = {
            # Computer Science & IT
            'Bachelor of Science in Computer Science': ['Artificial Intelligence', 'Machine Learning', 'Software Development', 'Data Science', 'Cybersecurity', 'Web Development'],
            'Bachelor of Science in Information Technology': ['Database Systems', 'Network Administration', 'Systems Analysis', 'Software Engineering', 'IT Support', 'Cloud Infrastructure'],
            'Master of Information Technology': ['AI Systems', 'Cloud Computing', 'Database Management', 'Network Security', 'IT Project Management', 'Enterprise Architecture'],
            'Doctor of Philosophy in Computer Science': ['Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Natural Language Processing', 'Computer Vision', 'Robotics'],
            'Bachelor of Science in Information Systems': ['Business Analytics', 'Systems Integration', 'Information Management', 'Digital Transformation', 'Process Automation'],

            # Engineering
            'Bachelor of Science in Civil Engineering': ['Structural Engineering', 'Construction Management', 'Transportation Engineering', 'Geotechnical Engineering', 'Water Resources'],
            'Bachelor of Science in Electrical Engineering': ['Power Systems', 'Control Systems', 'Renewable Energy', 'Electronics', 'Telecommunications'],
            'Bachelor of Science in Mechanical Engineering': ['Thermodynamics', 'Manufacturing Engineering', 'Machine Design', 'Automotive Engineering', 'Energy Systems'],
            'Master of Engineering': ['Sustainable Engineering', 'Project Engineering', 'Systems Engineering', 'Industrial Engineering', 'Infrastructure Development'],
            'Doctor of Philosophy in Engineering': ['Advanced Materials', 'Renewable Energy', 'Automation', 'Structural Analysis', 'Environmental Engineering'],
            
            # Education
            'Bachelor of Science in Education': ['Curriculum Development', 'Pedagogy', 'Educational Psychology', 'Classroom Management', 'Special Education'],
            'Bachelor of Early Childhood Education': ['Early Learning', 'Child Development', 'Inclusive Education', 'Play-Based Learning', 'Parent Engagement'],
            'Master of Education': ['Educational Leadership', 'Instructional Design', 'Educational Technology', 'Assessment and Evaluation', 'Teacher Training'],
            'Doctor of Philosophy in Education': ['Educational Research', 'Educational Policy', 'Higher Education Administration', 'Learning Sciences', 'Educational Innovation'],
            
            # Business & Management
            'Bachelor of Science in Business Administration': ['Business Management', 'Marketing', 'Operations Management', 'Strategic Planning', 'Entrepreneurship'],
            'Bachelor of Science in Human Resource Management': ['Talent Acquisition', 'Training and Development', 'Labor Relations', 'Compensation and Benefits', 'Organizational Development'],
            'Master of Business Administration': ['Strategic Management', 'Finance', 'Marketing Strategy', 'Leadership', 'Business Analytics'],
            'Bachelor of Science in Accountancy': ['Financial Accounting', 'Auditing', 'Tax Management', 'Cost Accounting', 'Financial Analysis'],
            'Master of Finance': ['Investment Analysis', 'Financial Modeling', 'Corporate Finance', 'Risk Management', 'Mergers and Acquisitions'],
            'Doctor of Philosophy in Business': ['Business Strategy', 'Organizational Behavior', 'International Business', 'Innovation Management', 'Corporate Governance'],
            
            # Health Sciences
            'Bachelor of Science in Nursing': ['Patient Care', 'Clinical Nursing', 'Community Health', 'Health Education', 'Medical-Surgical Nursing'],
            'Doctor of Medicine': ['Clinical Medicine', 'Public Health', 'Medical Research', 'Healthcare Management', 'Preventive Medicine'],
            'Master of Health Administration': ['Healthcare Management', 'Health Policy', 'Hospital Administration', 'Healthcare Quality', 'Health Informatics'],
            'Bachelor of Science in Pharmacy': ['Pharmacology', 'Pharmaceutical Care', 'Pharmacy Management', 'Clinical Pharmacy', 'Drug Safety'],

            # Environmental & Agricultural Sciences
            'Bachelor of Science in Environmental Science': ['Environmental Conservation', 'Climate Change', 'Sustainability', 'Ecology', 'Environmental Policy'],
            'Master of Environmental Science': ['Environmental Management', 'Conservation Biology', 'Renewable Resources', 'Environmental Impact Assessment', 'Green Technology'],
            'Bachelor of Science in Agriculture': ['Crop Production', 'Agricultural Economics', 'Sustainable Farming', 'Agribusiness', 'Soil Science'],
            'Master of Agricultural Technology': ['Agroecology', 'Precision Farming', 'Micro-Farming Systems', 'Agricultural Extension', 'Post-Harvest Technology'],

            # Social Sciences
            'Bachelor of Science in Psychology': ['Clinical Psychology', 'Counseling', 'Organizational Psychology', 'Child Development', 'Behavioral Science'],
            'Bachelor of Science in Social Work': ['Community Development', 'Social Welfare', 'Family Counseling', 'Crisis Intervention', 'Case Management'],
            'Master of Social Work': ['Community Development', 'Social Policy', 'Mental Health', 'Family Services', 'Social Justice'],
            'Master of Community Development': ['Community Organizing', 'Rural Development', 'Urban Planning', 'Participatory Development', 'Social Enterprise'],
            'Bachelor of Arts in Sociology': ['Cultural Studies', 'Social Theory', 'Human Behavior', 'Gender Studies', 'Population Studies'],

            # Public Administration & Law
            'Master of Public Administration': ['Public Policy', 'Governance', 'Public Management', 'Government Relations', 'Policy Analysis'],
            'Doctor of Public Administration': ['Public Governance', 'Policy Development', 'Public Sector Management', 'Administrative Law', 'Public Finance'],
            'Juris Doctor': ['Legal Practice', 'Constitutional Law', 'Corporate Law', 'Environmental Law', 'Human Rights Law'],
            'Bachelor of Laws': ['Civil Law', 'Criminal Law', 'Property Law', 'Commercial Law', 'Public International Law'],

            # Sciences
            'Bachelor of Science in Mathematics': ['Applied Mathematics', 'Statistics', 'Mathematical Modeling', 'Data Analysis', 'Quantitative Research'],
            'Bachelor of Science in Biology': ['Marine Biology', 'Ecology', 'Genetics', 'Microbiology', 'Conservation Biology'],
            'Bachelor of Science in Chemistry': ['Analytical Chemistry', 'Environmental Chemistry', 'Chemical Research', 'Materials Science', 'Quality Control'],
            'Bachelor of Science in Physics': ['Applied Physics', 'Renewable Energy', 'Materials Science', 'Computational Physics', 'Environmental Physics'],
            'Doctor of Philosophy in Science': ['Scientific Research', 'Environmental Science', 'Biotechnology', 'Marine Science', 'Climate Science'],

            # Architecture & Design
            'Bachelor of Science in Architecture': ['Architectural Design', 'Urban Planning', 'Sustainable Design', 'Building Technology', 'Landscape Architecture'],
            'Bachelor of Fine Arts': ['Graphic Design', 'Visual Communication', 'Illustration', 'Mixed Media', 'Studio Art'],
            'Bachelor of Interior Design': ['Interior Architecture', 'Space Planning', 'Design Aesthetics', 'Furniture Design', 'Sustainable Interiors'],

            # Tourism & Hospitality
            'Bachelor of Science in Tourism Management': ['Tourism Development', 'Hospitality Management', 'Event Management', 'Sustainable Tourism', 'Cultural Tourism'],
            'Bachelor of Science in Hotel and Restaurant Management': ['Food and Beverage Management', 'Culinary Arts', 'Hotel Operations', 'Hospitality Marketing', 'Customer Service'],

            # Languages & Communication
            'Bachelor of Arts in English': ['Communication', 'Technical Writing', 'Literature', 'English Language Teaching', 'Creative Writing'],
            'Bachelor of Arts in Communication': ['Media Relations', 'Public Relations', 'Digital Communication', 'Journalism', 'Corporate Communication'],
            'Bachelor of Arts in Journalism': ['News Reporting', 'Investigative Journalism', 'Editorial Writing', 'Digital Media Production', 'Broadcast Journalism'],

            # Project Management
            'Master of Project Management': ['Project Planning', 'Risk Management', 'Agile Methodologies', 'Stakeholder Management', 'Program Management'],
        }


        degree_expertise_pairs = []
        for degree, expertise_options in degree_expertise_map.items():
            for expertise in expertise_options:
                degree_expertise_pairs.append((degree, expertise))

        # Create Faculty Users
        self.stdout.write('Creating {} faculty users...'.format(faculty_user_count))
        faculty_users = []
        for i in range(1, faculty_user_count + 1):
            given_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            degree, expertise = random.choice(degree_expertise_pairs)
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=email,
                    given_name=given_name,
                    middle_initial=fake.random_uppercase_letter(),
                    last_name=last_name,
                    sex=random.choice([User.Sex.MALE, User.Sex.FEMALE]),
                    contact_no=f"09{random.randint(100000000, 999999999)}",
                    college=random.choice(colleges),
                    role=User.Role.FACULTY,
                    degree=degree,
                    expertise=expertise,
                    is_confirmed=True,
                    created_by=director,
                    created_at=timezone.now()
                )
                faculty_users.append(user)
            else:
                faculty_users.append(User.objects.get(email=email))
        self.stdout.write(self.style.SUCCESS(f"Created {len(faculty_users)} faculty users.\n"))

        # Get submission type downloadables
        file_templates = list(Downloadable.objects.filter(submission_type='file', is_submission_template=True))
        event_templates = list(Downloadable.objects.filter(submission_type='event', is_submission_template=True))
        final_templates = list(Downloadable.objects.filter(submission_type='final', is_submission_template=True))

        now = timezone.now()
        project_count = [0]  # Use list for mutability in inner function

        # Get Faculty U. Test user
        faculty_test_user = User.objects.filter(role=User.Role.FACULTY, given_name='Faculty', last_name='Test').first()
        if not faculty_test_user:
            self.stdout.write(self.style.ERROR('Faculty U. Test user not found. Please run create_test_assets first.'))
            return

        # NOT_STARTED projects with random faculty
        for _ in range(5):
            leader = random.choice([u for u in faculty_users if u.role not in [User.Role.IMPLEMENTER, User.Role.CLIENT]])
            providers = random.sample(faculty_users, k=min(random.randint(2, 3), len(faculty_users)))
            project = self.create_project(
                status='NOT_STARTED',
                leader=leader,
                providers=providers,
                agendas=agendas,
                sdgs=sdgs,
                director=director,
                file_templates=file_templates,
                event_templates=event_templates,
                final_templates=final_templates,
                now=now,
                PLACEHOLDER_PDF_PATH=PLACEHOLDER_PDF_PATH,
                PLACEHOLDER_IMAGE_PATH=PLACEHOLDER_IMAGE_PATH
            )
            project_count[0] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created NOT_STARTED project: {project.title} (leader: {leader.get_full_name()})"))

        # NOT_STARTED projects with Faculty U. Test as leader
        self.create_projects_for_leader(faculty_test_user, 'NOT_STARTED', no_of_ns_faculty_projects, faculty_users, agendas, sdgs, director, file_templates, event_templates, final_templates, now, PLACEHOLDER_PDF_PATH, PLACEHOLDER_IMAGE_PATH, project_count)

        # IN_PROGRESS projects with random faculty
        for _ in range(no_of_ip_projects):
            leader = random.choice([u for u in faculty_users if u.role not in [User.Role.IMPLEMENTER, User.Role.CLIENT]])
            providers = random.sample(faculty_users, k=min(random.randint(2, 3), len(faculty_users)))
            project = self.create_project(
                status='IN_PROGRESS',
                leader=leader,
                providers=providers,
                agendas=agendas,
                sdgs=sdgs,
                director=director,
                file_templates=file_templates,
                event_templates=event_templates,
                final_templates=final_templates,
                now=now,
                PLACEHOLDER_PDF_PATH=PLACEHOLDER_PDF_PATH,
                PLACEHOLDER_IMAGE_PATH=PLACEHOLDER_IMAGE_PATH
            )
            project_count[0] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created IN_PROGRESS project: {project.title} (leader: {leader.get_full_name()})"))

        # IN_PROGRESS projects with Faculty U. Test as leader
        self.create_projects_for_leader(faculty_test_user, 'IN_PROGRESS', no_of_ip_faculty_projects, faculty_users, agendas, sdgs, director, file_templates, event_templates, final_templates, now, PLACEHOLDER_PDF_PATH, PLACEHOLDER_IMAGE_PATH, project_count)

        # COMPLETED projects with random faculty
        for _ in range(no_of_c_projects):
            leader = random.choice([u for u in faculty_users if u.role not in [User.Role.IMPLEMENTER, User.Role.CLIENT]])
            providers = random.sample(faculty_users, k=min(random.randint(2, 3), len(faculty_users)))
            project = self.create_project(
                status='COMPLETED',
                leader=leader,
                providers=providers,
                agendas=agendas,
                sdgs=sdgs,
                director=director,
                file_templates=file_templates,
                event_templates=event_templates,
                final_templates=final_templates,
                now=now,
                PLACEHOLDER_PDF_PATH=PLACEHOLDER_PDF_PATH,
                PLACEHOLDER_IMAGE_PATH=PLACEHOLDER_IMAGE_PATH
            )
            project_count[0] += 1
            self.stdout.write(self.style.SUCCESS(f"  Created COMPLETED project: {project.title} (leader: {leader.get_full_name()})"))

        # COMPLETED projects with Faculty U. Test as leader
        self.create_projects_for_leader(faculty_test_user, 'COMPLETED', no_of_c_faculty_projects, faculty_users, agendas, sdgs, director, file_templates, event_templates, final_templates, now, PLACEHOLDER_PDF_PATH, PLACEHOLDER_IMAGE_PATH, project_count)


        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {project_count} projects with realistic data!'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {faculty_user_count} faculty users (email = password)'))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'   - NOT_STARTED: {no_of_ns_projects} project (future dates)')
        self.stdout.write(f'   - NOT_STARTED (Faculty U. Test as leader): {no_of_ns_faculty_projects} project (future dates)')
        self.stdout.write(f'   - IN_PROGRESS: {no_of_ip_projects} project (with events and submissions)')
        self.stdout.write(f'   - IN_PROGRESS (Faculty U. Test as leader): {no_of_ip_faculty_projects} project (with events and submissions)')
        self.stdout.write(f'   - COMPLETED: {no_of_c_projects} project (all events and submissions done)')
        self.stdout.write(f'   - COMPLETED (Faculty U. Test as leader): {no_of_c_faculty_projects} project (all events and submissions done)')
        self.stdout.write(self.style.SUCCESS('\n🎉 All Local test data generated successfully using actual media/static files!'))