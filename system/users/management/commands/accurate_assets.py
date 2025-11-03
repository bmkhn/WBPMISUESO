from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from system.users.models import College, Campus
from shared.projects.models import Project, ProjectDocument, ProjectEvent, SustainableDevelopmentGoal
from internal.submissions.models import Submission
from shared.downloadables.models import Downloadable
from internal.agenda.models import Agenda
from shared.request.models import ClientRequest
from django.utils import timezone
from django.core.files import File
from datetime import timedelta
import random
import os
from django.conf import settings
from faker import Faker

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Generate accurate test data with proper relationships and realistic statuses"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting accurate asset generation...'))

        faculty_user_count = 50
        client_user_count = 10
        not_started_projects = 5
        in_progress_projects = 5
        completed_projects = 5

        # Get existing data
        colleges = list(College.objects.all())
        agendas = list(Agenda.objects.all())
        sdgs = list(SustainableDevelopmentGoal.objects.all())
        downloadables = list(Downloadable.objects.all())
        
        if not colleges:
            self.stdout.write(self.style.ERROR('No colleges found. Run create_test_assets first.'))
            return
        
        if not agendas:
            self.stdout.write(self.style.ERROR('No agendas found. Run create_test_assets first.'))
            return
            
        if not downloadables:
            self.stdout.write(self.style.ERROR('No downloadables found. Run create_test_assets first.'))
            return
        
        # Get director for project creation
        director = User.objects.filter(role=User.Role.DIRECTOR).first()
        if not director:
            self.stdout.write(self.style.ERROR('No director found. Run create_test_assets first.'))
            return
        
        # Degree to expertise mapping for Faculty users
        degree_expertise_map = {
            # Computer Science & IT
            'Bachelor of Science in Computer Science': ['Artificial Intelligence', 'Machine Learning', 'Software Development', 'Data Science', 'Cybersecurity', 'Web Development'],
            'Master of Information Technology': ['Artificial Intelligence', 'Cloud Computing', 'Database Management', 'Network Security', 'Software Engineering', 'IT Project Management'],
            'Doctor of Philosophy in Computer Science': ['Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Natural Language Processing', 'Computer Vision', 'Robotics'],
            
            # Engineering
            'Bachelor of Science in Civil Engineering': ['Structural Engineering', 'Construction Management', 'Transportation Engineering', 'Geotechnical Engineering', 'Water Resources'],
            'Master of Engineering': ['Sustainable Engineering', 'Project Engineering', 'Systems Engineering', 'Industrial Engineering', 'Infrastructure Development'],
            'Doctor of Philosophy in Engineering': ['Advanced Materials', 'Renewable Energy', 'Automation', 'Structural Analysis', 'Environmental Engineering'],
            
            # Education
            'Bachelor of Science in Education': ['Curriculum Development', 'Pedagogy', 'Educational Psychology', 'Classroom Management', 'Special Education'],
            'Master of Education': ['Educational Leadership', 'Instructional Design', 'Educational Technology', 'Assessment and Evaluation', 'Teacher Training'],
            'Doctor of Philosophy in Education': ['Educational Research', 'Educational Policy', 'Higher Education Administration', 'Learning Sciences', 'Educational Innovation'],
            
            # Business & Management
            'Bachelor of Science in Business Administration': ['Business Management', 'Marketing', 'Operations Management', 'Strategic Planning', 'Entrepreneurship'],
            'Master of Business Administration': ['Strategic Management', 'Finance', 'Marketing Strategy', 'Leadership', 'Business Analytics'],
            'Bachelor of Science in Accountancy': ['Financial Accounting', 'Auditing', 'Tax Management', 'Cost Accounting', 'Financial Analysis'],
            'Doctor of Philosophy in Business': ['Business Strategy', 'Organizational Behavior', 'International Business', 'Innovation Management', 'Corporate Governance'],
            
            # Health Sciences
            'Bachelor of Science in Nursing': ['Patient Care', 'Clinical Nursing', 'Community Health', 'Health Education', 'Medical-Surgical Nursing'],
            'Doctor of Medicine': ['Clinical Medicine', 'Public Health', 'Medical Research', 'Healthcare Management', 'Preventive Medicine'],
            'Master of Health Administration': ['Healthcare Management', 'Health Policy', 'Hospital Administration', 'Healthcare Quality', 'Health Informatics'],
            
            # Environmental & Agricultural Sciences
            'Bachelor of Science in Environmental Science': ['Environmental Conservation', 'Climate Change', 'Sustainability', 'Ecology', 'Environmental Policy'],
            'Master of Environmental Science': ['Environmental Management', 'Conservation Biology', 'Renewable Resources', 'Environmental Impact Assessment', 'Green Technology'],
            'Bachelor of Science in Agriculture': ['Crop Production', 'Agricultural Economics', 'Sustainable Farming', 'Agribusiness', 'Soil Science'],
            
            # Social Sciences
            'Bachelor of Science in Psychology': ['Clinical Psychology', 'Counseling', 'Organizational Psychology', 'Child Development', 'Behavioral Science'],
            'Bachelor of Science in Social Work': ['Community Development', 'Social Welfare', 'Family Counseling', 'Crisis Intervention', 'Case Management'],
            'Master of Social Work': ['Community Development', 'Social Policy', 'Mental Health', 'Family Services', 'Social Justice'],
            'Master of Community Development': ['Community Organizing', 'Rural Development', 'Urban Planning', 'Participatory Development', 'Social Enterprise'],
            
            # Public Administration & Law
            'Master of Public Administration': ['Public Policy', 'Governance', 'Public Management', 'Government Relations', 'Policy Analysis'],
            'Doctor of Public Administration': ['Public Governance', 'Policy Development', 'Public Sector Management', 'Administrative Law', 'Public Finance'],
            'Juris Doctor': ['Legal Practice', 'Constitutional Law', 'Corporate Law', 'Environmental Law', 'Human Rights Law'],
            
            # Sciences
            'Bachelor of Science in Mathematics': ['Applied Mathematics', 'Statistics', 'Mathematical Modeling', 'Data Analysis', 'Quantitative Research'],
            'Bachelor of Science in Biology': ['Marine Biology', 'Ecology', 'Genetics', 'Microbiology', 'Conservation Biology'],
            'Bachelor of Science in Chemistry': ['Analytical Chemistry', 'Environmental Chemistry', 'Chemical Research', 'Materials Science', 'Quality Control'],
            'Bachelor of Science in Physics': ['Applied Physics', 'Renewable Energy', 'Materials Science', 'Computational Physics', 'Environmental Physics'],
            'Doctor of Philosophy in Science': ['Scientific Research', 'Environmental Science', 'Biotechnology', 'Marine Science', 'Climate Science'],
            
            # Architecture & Design
            'Bachelor of Science in Architecture': ['Architectural Design', 'Urban Planning', 'Sustainable Design', 'Building Technology', 'Landscape Architecture'],
            
            # Tourism & Hospitality
            'Bachelor of Science in Tourism Management': ['Tourism Development', 'Hospitality Management', 'Event Management', 'Sustainable Tourism', 'Cultural Tourism'],
            
            # Languages & Communication
            'Bachelor of Arts in English': ['Communication', 'Technical Writing', 'Literature', 'English Language Teaching', 'Creative Writing'],
            'Bachelor of Arts in Communication': ['Media Relations', 'Public Relations', 'Digital Communication', 'Journalism', 'Corporate Communication'],
            
            # Project Management
            'Master of Project Management': ['Project Planning', 'Risk Management', 'Agile Methodologies', 'Stakeholder Management', 'Program Management'],
        }
        
        # Get all available degree-expertise pairs
        degree_expertise_pairs = []
        for degree, expertise_options in degree_expertise_map.items():
            for expertise in expertise_options:
                degree_expertise_pairs.append((degree, expertise))

        # Create X Faculty users (using Faker for realistic data)
        
        self.stdout.write('Creating {} faculty users...'.format(faculty_user_count))
        faculty_users = []
        for i in range(1, faculty_user_count + 1):
            given_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()
            base_username = email.split('@')[0]
            username = base_username
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
        self.stdout.write(self.style.SUCCESS(f"Created {len(faculty_users)} faculty users."))

        
        # Create X Client users (using Faker)
        self.stdout.write('Creating {} client users...'.format(client_user_count))
        client_users = []
        for i in range(1, int(client_user_count) + 1):
            given_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()
            base_username = email.split('@')[0]
            username = base_username
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=email,  # Password = email
                    given_name=given_name,
                    middle_initial=fake.random_uppercase_letter(),
                    last_name=last_name,
                    sex=random.choice([User.Sex.MALE, User.Sex.FEMALE]),
                    contact_no=f"09{random.randint(100000000, 999999999)}",
                    company=fake.company(),
                    industry=random.choice(['Agriculture', 'Education', 'Healthcare', 'Tourism', 'Technology']),
                    role=User.Role.CLIENT,
                    is_confirmed=True,
                    created_by=director,
                    created_at=timezone.now()
                )
                client_users.append(user)
            else:
                client_users.append(User.objects.get(email=email))
        self.stdout.write(self.style.SUCCESS(f"Created {len(client_users)} client users."))

        # Create Client Requests for each client user (1-2 requests per client)
        self.stdout.write('Creating client requests...')
        faker_loi_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
        request_count = 0
        
        for client in client_users:
            num_requests = random.randint(1, 2)
            for j in range(num_requests):
                days_ago = random.randint(1, 180)
                submitted_at = timezone.now() - timedelta(days=days_ago)
                
                # Random status
                status = random.choice(['RECEIVED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'ENDORSED'])
                
                client_request = ClientRequest.objects.create(
                    title=f"{fake.catch_phrase()} for {fake.city()}",
                    organization=client.company or fake.company(),
                    primary_location=fake.city() + ', ' + fake.state(),
                    primary_beneficiary=random.choice(['Youth', 'Farmers', 'Women', 'Indigenous People', 'Senior Citizens', 'Students', 'Community Members']),
                    summary=fake.paragraph(nb_sentences=5),
                    submitted_by=client,
                    submitted_at=submitted_at,
                    status=status,
                )
                
                # Attach letter of intent
                if os.path.exists(faker_loi_path):
                    with open(faker_loi_path, 'rb') as f:
                        client_request.letter_of_intent.save('Letter of Intent.docx', File(f), save=True)
                
                # Set reviewed_by and timestamps based on status
                if status in ['UNDER_REVIEW', 'APPROVED', 'REJECTED', 'ENDORSED']:
                    client_request.reviewed_by = director
                    client_request.review_at = submitted_at + timedelta(days=random.randint(1, 5))
                    client_request.updated_by = director
                    client_request.updated_at = client_request.review_at
                    
                    if status in ['ENDORSED']:
                        client_request.endorsed_by = director
                        client_request.endorsed_at = client_request.review_at + timedelta(days=random.randint(1, 3))
                    
                    if status == 'REJECTED':
                        client_request.reason = fake.sentence(nb_words=10)
                    
                    client_request.save()
                
                request_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Created {request_count} client requests."))

        # Get submission type downloadables
        file_templates = list(Downloadable.objects.filter(submission_type='file', is_submission_template=True))
        event_templates = list(Downloadable.objects.filter(submission_type='event', is_submission_template=True))
        final_templates = list(Downloadable.objects.filter(submission_type='final', is_submission_template=True))
        
        # Create projects with different statuses
        self.stdout.write('\nCreating projects with realistic statuses...')
        
        now = timezone.now()
        project_count = 0
        
        # NOT_STARTED projects (X) - Future start date
        for i in range(not_started_projects):
            start_date = now.date() + timedelta(days=random.randint(30, 90))
            end_date = start_date + timedelta(days=random.randint(180, 365))
            
            leader = random.choice([u for u in faculty_users if u.role not in [User.Role.IMPLEMENTER, User.Role.CLIENT]])
            providers = random.sample(faculty_users, k=random.randint(2, 5))
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Training Program', 'Workshop Series', 'Community Seminar', 'Extension Service'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=random.randint(3, 8),
                event_progress=0,
                estimated_trainees=random.randint(50, 200),
                total_trained_individuals=0,
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido']),
                logistics_type=random.choice(['INTERNAL', 'EXTERNAL', 'BOTH']),
                internal_budget=random.randint(50000, 200000),
                external_budget=random.randint(0, 150000) if random.random() > 0.5 else 0,
                start_date=start_date,
                estimated_end_date=end_date,
                status='NOT_STARTED',
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))
            
            # Add proposal document
            faker_proposal_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
            if os.path.exists(faker_proposal_path):
                proposal_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='PROPOSAL',
                    description='Project Proposal Document'
                )
                with open(faker_proposal_path, 'rb') as f:
                    proposal_doc.file.save('Project_Proposal.docx', File(f), save=True)
                project.proposal_document = proposal_doc
                project.save(update_fields=['proposal_document'])
            
            # Add 1-2 additional documents
            for doc_num in range(random.randint(1, 2)):
                if os.path.exists(faker_proposal_path):
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        document_type='ADDITIONAL',
                        description=f'Additional Document {doc_num + 1}'
                    )
                    with open(faker_proposal_path, 'rb') as f:
                        add_doc.file.save(f'Additional_Document_{doc_num + 1}.docx', File(f), save=True)
                    project.additional_documents.add(add_doc)
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Created NOT_STARTED project: {project.title}"))
        

        # IN_PROGRESS projects (X) - Between start and end date, with events and submissions
        for i in range(in_progress_projects):
            days_ago = random.randint(30, 120)
            start_date = (now - timedelta(days=days_ago)).date()
            end_date = start_date + timedelta(days=random.randint(180, 365))
            
            leader = random.choice([u for u in faculty_users if u.role not in [User.Role.IMPLEMENTER, User.Role.CLIENT]])
            providers = random.sample(faculty_users, k=random.randint(2, 5))
            
            estimated_events = random.randint(4, 8)
            completed_events = random.randint(1, estimated_events - 1)  # Some completed, some remaining
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Skills Training', 'Community Workshop', 'Extension Program', 'Outreach Activity'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=estimated_events,
                event_progress=completed_events,
                estimated_trainees=random.randint(50, 200),
                total_trained_individuals=random.randint(20, 100),
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Barangay Officials']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'San Vicente', 'Brooke\'s Point']),
                logistics_type=random.choice(['INTERNAL', 'EXTERNAL', 'BOTH']),
                internal_budget=random.randint(50000, 300000),
                external_budget=random.randint(0, 200000) if random.random() > 0.5 else 0,
                start_date=start_date,
                estimated_end_date=end_date,
                status='IN_PROGRESS',
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))
            
            # Add proposal document
            faker_proposal_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
            if os.path.exists(faker_proposal_path):
                proposal_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='PROPOSAL',
                    description='Project Proposal Document'
                )
                with open(faker_proposal_path, 'rb') as f:
                    proposal_doc.file.save('Project_Proposal.docx', File(f), save=True)
                project.proposal_document = proposal_doc
                project.save(update_fields=['proposal_document'])
            
            # Add 1-3 additional documents
            for doc_num in range(random.randint(1, 3)):
                if os.path.exists(faker_proposal_path):
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        document_type='ADDITIONAL',
                        description=f'Additional Document {doc_num + 1}'
                    )
                    with open(faker_proposal_path, 'rb') as f:
                        add_doc.file.save(f'Additional_Document_{doc_num + 1}.docx', File(f), save=True)
                    project.additional_documents.add(add_doc)
            
            # Create events for in-progress projects
            for j in range(estimated_events):
                days_offset = random.randint(0, days_ago)
                event_date = now - timedelta(days=days_offset)
                
                # Determine event status based on whether it's completed
                if j < completed_events:
                    event_status = 'COMPLETED'
                elif j == completed_events and random.random() > 0.5:
                    event_status = 'ONGOING'
                else:
                    event_status = 'SCHEDULED'
                
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"Event {j+1}: {random.choice(['Training Session', 'Workshop', 'Seminar', 'Consultation', 'Field Visit'])}",
                    description=f"Activity description for event {j+1}",
                    datetime=event_date,
                    location=project.primary_location,
                    status=event_status,
                    has_submission=j < completed_events,  # Completed events have submissions
                    placeholder=False,
                    created_by=leader,
                    updated_by=leader,
                )
                
                # Create event submission if event is completed
                if j < completed_events and event_templates:
                    submitter = random.choice([leader] + list(project.providers.all()))
                    
                    # Get coordinator from the same college as project leader
                    coordinator = User.objects.filter(
                        role=User.Role.COORDINATOR,
                        college=leader.college
                    ).first()
                    
                    # Use Faker Event.docx file
                    faker_event_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker Event.docx')
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(event_templates),
                        deadline=event_date + timedelta(days=7),  # event_date is already timezone-aware
                        notes=f"Event documentation for {event.title}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(20, 80),
                        image_description=f"Photo from {event.title}",
                        status='APPROVED',  # Approved to contribute to progress
                        reviewed_by=coordinator if coordinator else director,  # Coordinator reviews
                        reviewed_at=event_date + timedelta(days=random.randint(6, 8)),
                        authorized_by=director,  # Director approves
                        authorized_at=event_date + timedelta(days=random.randint(9, 10)),
                        updated_by=director,
                    )
                    
                    # Attach the event file
                    if os.path.exists(faker_event_path):
                        with open(faker_event_path, 'rb') as f:
                            submission.file.save('Faker Event.docx', File(f), save=True)
                    
                    # Attach random image
                    image_files = ['background.png', 'image.png', 'lightbg.jpg']
                    random_image = random.choice(image_files)
                    image_path = os.path.join(settings.MEDIA_ROOT, 'faker', random_image)
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            submission.image_event.save(random_image, File(f), save=True)
            
            # Create some file submissions (monitoring, evaluation, etc.)
            if file_templates:
                num_file_submissions = random.randint(2, 4)
                faker_file_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
                
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                for k in range(num_file_submissions):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    # Convert date to timezone-aware datetime
                    deadline_date = start_date + timedelta(days=random.randint(30, days_ago))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    
                    # Random status for file submissions
                    status_choices = ['SUBMITTED', 'FORWARDED', 'APPROVED', 'REVISION_REQUESTED']
                    status = random.choice(status_choices)
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Required documentation {k+1}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status=status,
                        reviewed_by=coordinator if coordinator and status != 'SUBMITTED' else (director if status != 'SUBMITTED' else None),
                        reviewed_at=deadline - timedelta(days=1) if status != 'SUBMITTED' else None,
                        authorized_by=director if status in ['FORWARDED', 'APPROVED'] else None,
                        authorized_at=deadline if status in ['FORWARDED', 'APPROVED'] else None,
                        updated_by=director,
                    )
                    
                    # Attach the file
                    if os.path.exists(faker_file_path):
                        with open(faker_file_path, 'rb') as f:
                            submission.file.save('Faker File.docx', File(f), save=True)
                    
                    if status == 'REVISION_REQUESTED':
                        submission.reason_for_revision = "Please provide more detailed information."
                        submission.revision_count = random.randint(1, 2)
                        submission.save()
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Created IN_PROGRESS project: {project.title} ({estimated_events} events, {completed_events} completed)"))
        
        
        # COMPLETED projects (X) - Past dates, all events and submissions completed
        for i in range(completed_projects):
            days_ago = random.randint(180, 365)
            start_date = (now - timedelta(days=days_ago)).date()
            duration = random.randint(90, 180)
            end_date = start_date + timedelta(days=duration)
            
            leader = random.choice([u for u in faculty_users if u.role not in [User.Role.IMPLEMENTER, User.Role.CLIENT]])
            providers = random.sample(faculty_users, k=random.randint(2, 5))
            
            estimated_events = random.randint(3, 6)
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Community Development', 'Skills Enhancement', 'Livelihood Program', 'Health Initiative'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=estimated_events,
                event_progress=estimated_events,  # All events completed
                estimated_trainees=random.randint(100, 300),
                total_trained_individuals=random.randint(100, 300),
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Indigenous Groups']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'Narra', 'Quezon']),
                logistics_type=random.choice(['INTERNAL', 'EXTERNAL', 'BOTH']),
                internal_budget=random.randint(100000, 400000),
                external_budget=random.randint(0, 300000) if random.random() > 0.5 else 0,
                start_date=start_date,
                estimated_end_date=end_date,
                status='COMPLETED',
                has_final_submission=True,
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 5)))
            
            # Add proposal document
            faker_proposal_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
            if os.path.exists(faker_proposal_path):
                proposal_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='PROPOSAL',
                    description='Project Proposal Document'
                )
                with open(faker_proposal_path, 'rb') as f:
                    proposal_doc.file.save('Project_Proposal.docx', File(f), save=True)
                project.proposal_document = proposal_doc
                project.save(update_fields=['proposal_document'])
            
            # Add 2-4 additional documents
            for doc_num in range(random.randint(2, 4)):
                if os.path.exists(faker_proposal_path):
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        document_type='ADDITIONAL',
                        description=f'Additional Document {doc_num + 1}'
                    )
                    with open(faker_proposal_path, 'rb') as f:
                        add_doc.file.save(f'Additional_Document_{doc_num + 1}.docx', File(f), save=True)
                    project.additional_documents.add(add_doc)
            
            # Create all events as completed
            for j in range(estimated_events):
                days_offset = random.randint(0, duration - 10)
                event_date = timezone.make_aware(timezone.datetime.combine(start_date + timedelta(days=days_offset), timezone.datetime.min.time()))
                
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"Event {j+1}: {random.choice(['Training Session', 'Workshop', 'Seminar', 'Technical Assistance', 'Monitoring Visit'])}",
                    description=f"Completed activity for {project.title}",
                    datetime=event_date,
                    location=project.primary_location,
                    status='COMPLETED',
                    has_submission=True,
                    placeholder=False,
                    created_by=leader,
                    updated_by=leader,
                )
                
                # Create event submission (all approved)
                if event_templates:
                    submitter = random.choice([leader] + list(project.providers.all()))
                    faker_event_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker Event.docx')
                    
                    # Get coordinator from the same college as project leader
                    coordinator = User.objects.filter(
                        role=User.Role.COORDINATOR,
                        college=leader.college
                    ).first()
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(event_templates),
                        deadline=event_date + timedelta(days=7),
                        notes=f"Event documentation for {event.title}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(30, 60),
                        image_description=f"Documentation photo from {event.title}",
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,  # Coordinator reviews
                        reviewed_at=event_date + timedelta(days=random.randint(6, 7)),
                        authorized_by=director,  # Director approves
                        authorized_at=event_date + timedelta(days=random.randint(8, 10)),
                        updated_by=director,
                    )
                    
                    # Attach the event file
                    if os.path.exists(faker_event_path):
                        with open(faker_event_path, 'rb') as f:
                            submission.file.save('Faker Event.docx', File(f), save=True)
                    
                    # Attach random image
                    image_files = ['background.png', 'image.png', 'lightbg.jpg']
                    random_image = random.choice(image_files)
                    image_path = os.path.join(settings.MEDIA_ROOT, 'faker', random_image)
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            submission.image_event.save(random_image, File(f), save=True)
            
            # Create all required file submissions (all approved)
            if file_templates:
                faker_file_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
                
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                for k in range(3):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    # Convert date to timezone-aware datetime
                    deadline_date = end_date - timedelta(days=random.randint(10, 30))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Monitoring document {k+1}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,  # Coordinator reviews
                        reviewed_at=deadline,
                        authorized_by=director,  # Director approves
                        authorized_at=deadline + timedelta(days=1),
                        updated_by=director,
                    )
                    
                    # Attach the file
                    if os.path.exists(faker_file_path):
                        with open(faker_file_path, 'rb') as f:
                            submission.file.save('Faker File.docx', File(f), save=True)
            
            # Create final submission (accomplishment report)
            if final_templates:
                submitter = leader
                # Convert date to timezone-aware datetime
                deadline_date = end_date + timedelta(days=7)
                deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                faker_final_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker Final.docx')
                
                submission = Submission.objects.create(
                    project=project,
                    downloadable=random.choice(final_templates),
                    deadline=deadline,
                    notes="Final accomplishment report",
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
                
                # Attach the final file
                if os.path.exists(faker_final_path):
                    with open(faker_final_path, 'rb') as f:
                        submission.file.save('Faker Final.docx', File(f), save=True)
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Created COMPLETED project: {project.title} (All {estimated_events} events completed)"))

  
#################################################################################################################################################################################

        self.stdout.write('\nCreating projects with realistic statuses where Test Faculty is Leader...')

        # WHERE TEST FACULTY IS THE LEADER
        # NOT_STARTED projects (X) - Future start date
        for i in range(not_started_projects):
            start_date = now.date() + timedelta(days=random.randint(30, 90))
            end_date = start_date + timedelta(days=random.randint(180, 365))

            leader = User.objects.filter(role=User.Role.FACULTY).first()
            providers = random.sample(faculty_users, k=min(random.randint(2, 5), len(faculty_users)))

            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Training Program', 'Workshop Series', 'Community Seminar', 'Extension Service'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=random.randint(3, 8),
                event_progress=0,
                estimated_trainees=random.randint(50, 200),
                total_trained_individuals=0,
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido']),
                logistics_type=random.choice(['INTERNAL', 'EXTERNAL', 'BOTH']),
                internal_budget=random.randint(50000, 200000),
                external_budget=random.randint(0, 150000) if random.random() > 0.5 else 0,
                start_date=start_date,
                estimated_end_date=end_date,
                status='NOT_STARTED',
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))
            
            # Add proposal document
            faker_proposal_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
            if os.path.exists(faker_proposal_path):
                proposal_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='PROPOSAL',
                    description='Project Proposal Document'
                )
                with open(faker_proposal_path, 'rb') as f:
                    proposal_doc.file.save('Project_Proposal.docx', File(f), save=True)
                project.proposal_document = proposal_doc
                project.save(update_fields=['proposal_document'])
            
            # Add 1-2 additional documents
            for doc_num in range(random.randint(1, 2)):
                if os.path.exists(faker_proposal_path):
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        document_type='ADDITIONAL',
                        description=f'Additional Document {doc_num + 1}'
                    )
                    with open(faker_proposal_path, 'rb') as f:
                        add_doc.file.save(f'Additional_Document_{doc_num + 1}.docx', File(f), save=True)
                    project.additional_documents.add(add_doc)
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Created NOT_STARTED project: {project.title}"))
        

        # IN_PROGRESS projects (X) - Between start and end date, with events and submissions
        for i in range(in_progress_projects):
            days_ago = random.randint(30, 120)
            start_date = (now - timedelta(days=days_ago)).date()
            end_date = start_date + timedelta(days=random.randint(180, 365))
            
            leader = User.objects.filter(role=User.Role.FACULTY).first()
            providers = random.sample(faculty_users, k=min(random.randint(2, 5), len(faculty_users)))
            
            estimated_events = random.randint(4, 8)
            completed_events = random.randint(1, estimated_events - 1)  # Some completed, some remaining
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Skills Training', 'Community Workshop', 'Extension Program', 'Outreach Activity'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=estimated_events,
                event_progress=completed_events,
                estimated_trainees=random.randint(50, 200),
                total_trained_individuals=random.randint(20, 100),
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Barangay Officials']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'San Vicente', 'Brooke\'s Point']),
                logistics_type=random.choice(['INTERNAL', 'EXTERNAL', 'BOTH']),
                internal_budget=random.randint(50000, 300000),
                external_budget=random.randint(0, 200000) if random.random() > 0.5 else 0,
                start_date=start_date,
                estimated_end_date=end_date,
                status='IN_PROGRESS',
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))
            
            # Add proposal document
            faker_proposal_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
            if os.path.exists(faker_proposal_path):
                proposal_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='PROPOSAL',
                    description='Project Proposal Document'
                )
                with open(faker_proposal_path, 'rb') as f:
                    proposal_doc.file.save('Project_Proposal.docx', File(f), save=True)
                project.proposal_document = proposal_doc
                project.save(update_fields=['proposal_document'])
            
            # Add 1-3 additional documents
            for doc_num in range(random.randint(1, 3)):
                if os.path.exists(faker_proposal_path):
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        document_type='ADDITIONAL',
                        description=f'Additional Document {doc_num + 1}'
                    )
                    with open(faker_proposal_path, 'rb') as f:
                        add_doc.file.save(f'Additional_Document_{doc_num + 1}.docx', File(f), save=True)
                    project.additional_documents.add(add_doc)
            
            # Create events for in-progress projects
            for j in range(estimated_events):
                days_offset = random.randint(0, days_ago)
                event_date = now - timedelta(days=days_offset)
                
                # Determine event status based on whether it's completed
                if j < completed_events:
                    event_status = 'COMPLETED'
                elif j == completed_events and random.random() > 0.5:
                    event_status = 'ONGOING'
                else:
                    event_status = 'SCHEDULED'
                
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"Event {j+1}: {random.choice(['Training Session', 'Workshop', 'Seminar', 'Consultation', 'Field Visit'])}",
                    description=f"Activity description for event {j+1}",
                    datetime=event_date,
                    location=project.primary_location,
                    status=event_status,
                    has_submission=j < completed_events,  # Completed events have submissions
                    placeholder=False,
                    created_by=leader,
                    updated_by=leader,
                )
                
                # Create event submission if event is completed
                if j < completed_events and event_templates:
                    submitter = random.choice([leader] + list(project.providers.all()))
                    
                    # Get coordinator from the same college as project leader
                    coordinator = User.objects.filter(
                        role=User.Role.COORDINATOR,
                        college=leader.college
                    ).first()
                    
                    # Use Faker Event.docx file
                    faker_event_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker Event.docx')
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(event_templates),
                        deadline=event_date + timedelta(days=7),  # event_date is already timezone-aware
                        notes=f"Event documentation for {event.title}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(20, 80),
                        image_description=f"Photo from {event.title}",
                        status='APPROVED',  # Approved to contribute to progress
                        reviewed_by=coordinator if coordinator else director,  # Coordinator reviews
                        reviewed_at=event_date + timedelta(days=random.randint(6, 8)),
                        authorized_by=director,  # Director approves
                        authorized_at=event_date + timedelta(days=random.randint(9, 10)),
                        updated_by=director,
                    )
                    
                    # Attach the event file
                    if os.path.exists(faker_event_path):
                        with open(faker_event_path, 'rb') as f:
                            submission.file.save('Faker Event.docx', File(f), save=True)
                    
                    # Attach random image
                    image_files = ['background.png', 'image.png', 'lightbg.jpg']
                    random_image = random.choice(image_files)
                    image_path = os.path.join(settings.MEDIA_ROOT, 'faker', random_image)
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            submission.image_event.save(random_image, File(f), save=True)
            
            # Create some file submissions (monitoring, evaluation, etc.)
            if file_templates:
                num_file_submissions = random.randint(2, 4)
                faker_file_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
                
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                for k in range(num_file_submissions):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    # Convert date to timezone-aware datetime
                    deadline_date = start_date + timedelta(days=random.randint(30, days_ago))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    
                    # Random status for file submissions
                    status_choices = ['SUBMITTED', 'FORWARDED', 'APPROVED', 'REVISION_REQUESTED']
                    status = random.choice(status_choices)
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Required documentation {k+1}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status=status,
                        reviewed_by=coordinator if coordinator and status != 'SUBMITTED' else (director if status != 'SUBMITTED' else None),
                        reviewed_at=deadline - timedelta(days=1) if status != 'SUBMITTED' else None,
                        authorized_by=director if status in ['FORWARDED', 'APPROVED'] else None,
                        authorized_at=deadline if status in ['FORWARDED', 'APPROVED'] else None,
                        updated_by=director,
                    )
                    
                    # Attach the file
                    if os.path.exists(faker_file_path):
                        with open(faker_file_path, 'rb') as f:
                            submission.file.save('Faker File.docx', File(f), save=True)
                    
                    if status == 'REVISION_REQUESTED':
                        submission.reason_for_revision = "Please provide more detailed information."
                        submission.revision_count = random.randint(1, 2)
                        submission.save()
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Created IN_PROGRESS project: {project.title} ({estimated_events} events, {completed_events} completed)"))
        
        
        # COMPLETED projects (X) - Past dates, all events and submissions completed
        for i in range(completed_projects):
            days_ago = random.randint(180, 365)
            start_date = (now - timedelta(days=days_ago)).date()
            duration = random.randint(90, 180)
            end_date = start_date + timedelta(days=duration)
            
            leader = User.objects.filter(role=User.Role.FACULTY).first()
            providers = random.sample(faculty_users, k=min(random.randint(2, 5), len(faculty_users)))
            
            estimated_events = random.randint(3, 6)
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Community Development', 'Skills Enhancement', 'Livelihood Program', 'Health Initiative'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=estimated_events,
                event_progress=estimated_events,  # All events completed
                estimated_trainees=random.randint(100, 300),
                total_trained_individuals=random.randint(100, 300),
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Indigenous Groups']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'Narra', 'Quezon']),
                logistics_type=random.choice(['INTERNAL', 'EXTERNAL', 'BOTH']),
                internal_budget=random.randint(100000, 400000),
                external_budget=random.randint(0, 300000) if random.random() > 0.5 else 0,
                start_date=start_date,
                estimated_end_date=end_date,
                status='COMPLETED',
                has_final_submission=True,
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 5)))
            
            # Add proposal document
            faker_proposal_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
            if os.path.exists(faker_proposal_path):
                proposal_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='PROPOSAL',
                    description='Project Proposal Document'
                )
                with open(faker_proposal_path, 'rb') as f:
                    proposal_doc.file.save('Project_Proposal.docx', File(f), save=True)
                project.proposal_document = proposal_doc
                project.save(update_fields=['proposal_document'])
            
            # Add 2-4 additional documents
            for doc_num in range(random.randint(2, 4)):
                if os.path.exists(faker_proposal_path):
                    add_doc = ProjectDocument.objects.create(
                        project=project,
                        document_type='ADDITIONAL',
                        description=f'Additional Document {doc_num + 1}'
                    )
                    with open(faker_proposal_path, 'rb') as f:
                        add_doc.file.save(f'Additional_Document_{doc_num + 1}.docx', File(f), save=True)
                    project.additional_documents.add(add_doc)
            
            # Create all events as completed
            for j in range(estimated_events):
                days_offset = random.randint(0, duration - 10)
                event_date = timezone.make_aware(timezone.datetime.combine(start_date + timedelta(days=days_offset), timezone.datetime.min.time()))
                
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"Event {j+1}: {random.choice(['Training Session', 'Workshop', 'Seminar', 'Technical Assistance', 'Monitoring Visit'])}",
                    description=f"Completed activity for {project.title}",
                    datetime=event_date,
                    location=project.primary_location,
                    status='COMPLETED',
                    has_submission=True,
                    placeholder=False,
                    created_by=leader,
                    updated_by=leader,
                )
                
                # Create event submission (all approved)
                if event_templates:
                    submitter = random.choice([leader] + list(project.providers.all()))
                    faker_event_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker Event.docx')
                    
                    # Get coordinator from the same college as project leader
                    coordinator = User.objects.filter(
                        role=User.Role.COORDINATOR,
                        college=leader.college
                    ).first()
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(event_templates),
                        deadline=event_date + timedelta(days=7),
                        notes=f"Event documentation for {event.title}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(30, 60),
                        image_description=f"Documentation photo from {event.title}",
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,  # Coordinator reviews
                        reviewed_at=event_date + timedelta(days=random.randint(6, 7)),
                        authorized_by=director,  # Director approves
                        authorized_at=event_date + timedelta(days=random.randint(8, 10)),
                        updated_by=director,
                    )
                    
                    # Attach the event file
                    if os.path.exists(faker_event_path):
                        with open(faker_event_path, 'rb') as f:
                            submission.file.save('Faker Event.docx', File(f), save=True)
                    
                    # Attach random image
                    image_files = ['background.png', 'image.png', 'lightbg.jpg']
                    random_image = random.choice(image_files)
                    image_path = os.path.join(settings.MEDIA_ROOT, 'faker', random_image)
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            submission.image_event.save(random_image, File(f), save=True)
            
            # Create all required file submissions (all approved)
            if file_templates:
                faker_file_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker File.docx')
                
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                for k in range(3):
                    submitter = random.choice([leader] + list(project.providers.all()))
                    # Convert date to timezone-aware datetime
                    deadline_date = end_date - timedelta(days=random.randint(10, 30))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Monitoring document {k+1}",
                        created_by=director,
                        submitted_by=submitter,
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,  # Coordinator reviews
                        reviewed_at=deadline,
                        authorized_by=director,  # Director approves
                        authorized_at=deadline + timedelta(days=1),
                        updated_by=director,
                    )
                    
                    # Attach the file
                    if os.path.exists(faker_file_path):
                        with open(faker_file_path, 'rb') as f:
                            submission.file.save('Faker File.docx', File(f), save=True)
            
            # Create final submission (accomplishment report)
            if final_templates:
                submitter = leader
                # Convert date to timezone-aware datetime
                deadline_date = end_date + timedelta(days=7)
                deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                faker_final_path = os.path.join(settings.MEDIA_ROOT, 'faker', 'Faker Final.docx')
                
                submission = Submission.objects.create(
                    project=project,
                    downloadable=random.choice(final_templates),
                    deadline=deadline,
                    notes="Final accomplishment report",
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
                
                # Attach the final file
                if os.path.exists(faker_final_path):
                    with open(faker_final_path, 'rb') as f:
                        submission.file.save('Faker Final.docx', File(f), save=True)
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  Created COMPLETED project: {project.title} (All {estimated_events} events completed)"))
        


        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {project_count} projects with realistic data!'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {faculty_user_count} faculty users (email = password)'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {client_user_count} client users (email = password)'))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'   - NOT_STARTED: {not_started_projects * 2} projects (future dates)')
        self.stdout.write(f'   - IN_PROGRESS: {in_progress_projects * 2} projects (with events and submissions)')
        self.stdout.write(f'   - COMPLETED: {completed_projects * 2} projects (all events and submissions done)')
        self.stdout.write(self.style.SUCCESS('\n🎉 All test data generated successfully!'))
