from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from system.users.models import College, Campus
from shared.projects.models import Project, ProjectDocument, ProjectEvaluation, ProjectEvent, SustainableDevelopmentGoal
from internal.submissions.models import Submission
from shared.downloadables.models import Downloadable
from internal.agenda.models import Agenda
from django.utils import timezone
from datetime import timedelta
import random
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Generate test projects for Faculty U. Test user using placeholder URLs (no file uploads to volume)"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting Faculty U. Test project generation...\n'))

        # CONFIGURABLE COUNTS - Edit these to change amounts
        not_started_projects = 1
        in_progress_projects = 1
        completed_projects = 1

        # PLACEHOLDER URLS - Files already in Railway media
        PLACEHOLDER_PDF_URL = "https://uesopmis.up.railway.app/media/downloadables/files/Placeholder.pdf"
        PLACEHOLDER_IMAGE_URL = "https://uesopmis.up.railway.app/media/about_us/director/image.png"
        
        # These are relative paths from MEDIA_ROOT for Django FileField
        PLACEHOLDER_PDF_PATH = "downloadables/files/Placeholder.pdf"
        PLACEHOLDER_IMAGE_PATH = "about_us/director/image.png"

        # Get Faculty U. Test user
        faculty_user = User.objects.filter(
            role=User.Role.FACULTY,
            given_name='Faculty',
            last_name='Test'
        ).first()
        
        if not faculty_user:
            self.stdout.write(self.style.ERROR('Faculty U. Test user not found. Please run create_test_assets first.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found Faculty U. Test: {faculty_user.email}\n'))

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
        
        # Get other faculty users for providers
        other_faculty = list(User.objects.filter(role=User.Role.FACULTY).exclude(id=faculty_user.id)[:5])
        if not other_faculty:
            self.stdout.write(self.style.WARNING('No other faculty users found. Projects will have Faculty U. Test as sole provider.\n'))
            other_faculty = []
        
        # Get submission type downloadables
        file_templates = list(Downloadable.objects.filter(submission_type='file', is_submission_template=True))
        event_templates = list(Downloadable.objects.filter(submission_type='event', is_submission_template=True))
        final_templates = list(Downloadable.objects.filter(submission_type='final', is_submission_template=True))
        
        # Create projects with different statuses
        self.stdout.write('Creating projects with Faculty U. Test as leader...\n')
        
        now = timezone.now()
        project_count = 0
        
        # NOT_STARTED project (1) - Future start date
        for i in range(not_started_projects):
            start_date = now.date() + timedelta(days=random.randint(30, 90))
            end_date = start_date + timedelta(days=random.randint(180, 365))
            
            # Faculty U. Test is always the leader
            leader = faculty_user
            providers = [faculty_user] + random.sample(other_faculty, k=min(random.randint(1, 2), len(other_faculty)))
            
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

            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Training Program', 'Workshop Series', 'Community Seminar', 'Extension Service'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=random.randint(3, 5),
                event_progress=0,
                estimated_trainees=random.randint(50, 200),
                total_trained_individuals=0,
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido']),
                logistics_type=logistics_type,
                internal_budget=internal_budget,
                external_budget=external_budget,
                sponsor_name=sponsor_name,
                start_date=start_date,
                estimated_end_date=end_date,
                status='NOT_STARTED',
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))
            
            # Add proposal document using placeholder
            proposal_doc = ProjectDocument.objects.create(
                project=project,
                document_type='PROPOSAL',
                description='Project Proposal Document'
            )
            proposal_doc.file.name = PLACEHOLDER_PDF_PATH
            proposal_doc.save()
            project.proposal_document = proposal_doc
            project.save(update_fields=['proposal_document'])
            
            # Add 1-2 additional documents using placeholder
            for doc_num in range(random.randint(1, 2)):
                additional_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='ADDITIONAL',
                    description=f'Additional Document {doc_num + 1}'
                )
                additional_doc.file.name = PLACEHOLDER_PDF_PATH
                additional_doc.save()
                project.additional_documents.add(additional_doc)
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  ✅ Created NOT_STARTED project: {project.title}"))
        

        # IN_PROGRESS project (1) - Between start and end date, with events and submissions
        for i in range(in_progress_projects):
            days_ago = random.randint(30, 120)
            start_date = (now - timedelta(days=days_ago)).date()
            end_date = start_date + timedelta(days=random.randint(180, 365))
            
            # Faculty U. Test is always the leader
            leader = faculty_user
            providers = [faculty_user] + random.sample(other_faculty, k=min(random.randint(1, 2), len(other_faculty)))
            
            estimated_events = random.randint(4, 6)
            completed_events = random.randint(1, estimated_events - 1)  # Some completed, some remaining

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
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Skills Training', 'Community Workshop', 'Extension Program', 'Outreach Activity'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=estimated_events,
                event_progress=0,  # Will be set by signal when submissions are created
                estimated_trainees=random.randint(50, 200),
                total_trained_individuals=random.randint(20, 100),
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Barangay Officials']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'San Vicente', 'Brooke\'s Point']),
                logistics_type=logistics_type,
                internal_budget=internal_budget,
                external_budget=external_budget,
                sponsor_name=sponsor_name,
                start_date=start_date,
                estimated_end_date=end_date,
                status='IN_PROGRESS',
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 4)))
            
            # Add proposal document using placeholder
            proposal_doc = ProjectDocument.objects.create(
                project=project,
                document_type='PROPOSAL',
                description='Project Proposal Document'
            )
            proposal_doc.file.name = PLACEHOLDER_PDF_PATH
            proposal_doc.save()
            project.proposal_document = proposal_doc
            project.save(update_fields=['proposal_document'])
            
            # Add 1-3 additional documents using placeholder
            for doc_num in range(random.randint(1, 3)):
                additional_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='ADDITIONAL',
                    description=f'Additional Document {doc_num + 1}'
                )
                additional_doc.file.name = PLACEHOLDER_PDF_PATH
                additional_doc.save()
                project.additional_documents.add(additional_doc)
            
            # Create events for in-progress projects
            for j in range(estimated_events):
                # Events spread across project timeline
                days_offset = int((days_ago / estimated_events) * j)
                event_date = now - timedelta(days=days_ago - days_offset)
                
                # Determine event status
                if j < completed_events:
                    event_status = 'COMPLETED'
                    has_submission = True
                elif j == completed_events:
                    event_status = 'ONGOING'
                    has_submission = False
                else:
                    event_status = 'SCHEDULED'
                    has_submission = False
                
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"Event {j+1}: {fake.bs().title()}",
                    description=fake.paragraph(),
                    datetime=event_date,
                    location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido']),
                    status=event_status,
                    placeholder=False,
                    has_submission=has_submission,
                    created_by=director,
                    updated_by=director,
                )
                
                # Add event image using placeholder
                event.image.name = PLACEHOLDER_IMAGE_PATH
                event.save()
                
                # Create event submission ONLY for completed events
                if event_status == 'COMPLETED' and event_templates:
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
                        submitted_by=leader,  # Faculty U. Test submits
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(20, 80),
                        image_description=f"Photo from {event.title}",
                        status='APPROVED',  # APPROVED to contribute to progress
                        reviewed_by=coordinator if coordinator else director,
                        reviewed_at=event_date + timedelta(days=random.randint(6, 8)),
                        authorized_by=director,
                        authorized_at=event_date + timedelta(days=random.randint(9, 10)),
                        updated_by=director,
                    )
                    
                    # Attach placeholder file and image (signal will update event_progress)
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.image_event.name = PLACEHOLDER_IMAGE_PATH
                    submission.save()
            
            # Create some file submissions (monitoring, evaluation, etc.)
            if file_templates:
                num_file_submissions = random.randint(2, 3)
                
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                for k in range(num_file_submissions):
                    # Convert date to timezone-aware datetime
                    deadline_date = start_date + timedelta(days=random.randint(30, days_ago))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    
                    # Random status for file submissions
                    status_choices = ['SUBMITTED', 'FORWARDED', 'APPROVED']
                    status = random.choice(status_choices)
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Required documentation {k+1}",
                        created_by=director,
                        submitted_by=leader,  # Faculty U. Test submits
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status=status,
                        reviewed_by=coordinator if coordinator and status != 'SUBMITTED' else (director if status != 'SUBMITTED' else None),
                        reviewed_at=deadline - timedelta(days=1) if status != 'SUBMITTED' else None,
                        authorized_by=director if status in ['FORWARDED', 'APPROVED'] else None,
                        authorized_at=deadline if status in ['FORWARDED', 'APPROVED'] else None,
                        updated_by=director,
                    )
                    
                    # Attach placeholder file
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.save()
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  ✅ Created IN_PROGRESS project: {project.title} ({estimated_events} events, {completed_events} completed)"))
        
        
        # COMPLETED project (1) - Past dates, all events and submissions completed
        for i in range(completed_projects):
            days_ago = random.randint(180, 365)
            start_date = (now - timedelta(days=days_ago)).date()
            duration = random.randint(90, 180)
            end_date = start_date + timedelta(days=duration)
            
            # Faculty U. Test is always the leader
            leader = faculty_user
            providers = [faculty_user] + random.sample(other_faculty, k=min(random.randint(1, 2), len(other_faculty)))
            
            estimated_events = random.randint(3, 5)

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
            
            project = Project.objects.create(
                title=f"{fake.catch_phrase()} - {random.choice(['Community Development', 'Skills Enhancement', 'Livelihood Program', 'Health Initiative'])}",
                project_leader=leader,
                agenda=random.choice(agendas),
                project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
                estimated_events=estimated_events,
                event_progress=0,  # Will be set to estimated_events by signal when all event submissions are created
                estimated_trainees=random.randint(100, 300),
                total_trained_individuals=random.randint(100, 300),
                primary_beneficiary=random.choice(['Students', 'Farmers', 'Teachers', 'Community Members', 'LGU Officials', 'Indigenous Groups']),
                primary_location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'Narra', 'Quezon']),
                logistics_type=logistics_type,
                internal_budget=internal_budget,
                external_budget=external_budget,
                sponsor_name=sponsor_name,
                start_date=start_date,
                estimated_end_date=end_date,
                status='COMPLETED',
                has_final_submission=True,
                created_by=director,
                updated_by=director,
            )
            project.providers.set(providers)
            project.sdgs.set(random.sample(sdgs, k=random.randint(2, 5)))
            
            # Add proposal document using placeholder
            proposal_doc = ProjectDocument.objects.create(
                project=project,
                document_type='PROPOSAL',
                description='Project Proposal Document'
            )
            proposal_doc.file.name = PLACEHOLDER_PDF_PATH
            proposal_doc.save()
            project.proposal_document = proposal_doc
            project.save(update_fields=['proposal_document'])
            
            # Add 2-4 additional documents using placeholder
            for doc_num in range(random.randint(2, 4)):
                additional_doc = ProjectDocument.objects.create(
                    project=project,
                    document_type='ADDITIONAL',
                    description=f'Additional Document {doc_num + 1}'
                )
                additional_doc.file.name = PLACEHOLDER_PDF_PATH
                additional_doc.save()
                project.additional_documents.add(additional_doc)
            
            # Create all events as COMPLETED
            for j in range(estimated_events):
                # Events spread across project timeline
                days_offset = int((duration / estimated_events) * j)
                event_date = timezone.make_aware(timezone.datetime.combine(start_date + timedelta(days=days_offset), timezone.datetime.min.time()))
                
                event = ProjectEvent.objects.create(
                    project=project,
                    title=f"Event {j+1}: {fake.bs().title()}",
                    description=fake.paragraph(),
                    datetime=event_date,
                    location=random.choice(['Puerto Princesa', 'Roxas', 'Taytay', 'Coron', 'El Nido', 'Narra']),
                    status='COMPLETED',
                    placeholder=False,
                    has_submission=True,
                    created_by=director,
                    updated_by=director,
                )
                
                # Add event image using placeholder
                event.image.name = PLACEHOLDER_IMAGE_PATH
                event.save()
                
                # Create APPROVED event submission for each event (signal will update event_progress)
                if event_templates:
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
                        submitted_by=leader,  # Faculty U. Test submits
                        submitted_at=event_date + timedelta(days=random.randint(1, 5)),
                        event=event,
                        num_trained_individuals=random.randint(30, 100),
                        image_description=f"Photo from {event.title}",
                        status='APPROVED',  # APPROVED to count toward event_progress
                        reviewed_by=coordinator if coordinator else director,
                        reviewed_at=event_date + timedelta(days=random.randint(6, 8)),
                        authorized_by=director,
                        authorized_at=event_date + timedelta(days=random.randint(9, 10)),
                        updated_by=director,
                    )
                    
                    # Attach placeholder file and image
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.image_event.name = PLACEHOLDER_IMAGE_PATH
                    submission.save()
            
            # Create multiple file submissions (monitoring, evaluation, etc.)
            if file_templates:
                num_file_submissions = random.randint(3, 5)
                
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                for k in range(num_file_submissions):
                    # Convert date to timezone-aware datetime
                    deadline_date = start_date + timedelta(days=random.randint(30, duration))
                    deadline = timezone.make_aware(timezone.datetime.combine(deadline_date, timezone.datetime.min.time()))
                    
                    submission = Submission.objects.create(
                        project=project,
                        downloadable=random.choice(file_templates),
                        deadline=deadline,
                        notes=f"Required documentation {k+1}",
                        created_by=director,
                        submitted_by=leader,  # Faculty U. Test submits
                        submitted_at=deadline - timedelta(days=random.randint(1, 3)),
                        status='APPROVED',
                        reviewed_by=coordinator if coordinator else director,
                        reviewed_at=deadline - timedelta(days=1),
                        authorized_by=director,
                        authorized_at=deadline,
                        updated_by=director,
                    )
                    
                    # Attach placeholder file
                    submission.file.name = PLACEHOLDER_PDF_PATH
                    submission.save()
            
            # Create APPROVED final submission (signal will set has_final_submission=True)
            if final_templates:
                # Get coordinator from the same college as project leader
                coordinator = User.objects.filter(
                    role=User.Role.COORDINATOR,
                    college=leader.college
                ).first()
                
                final_deadline = timezone.make_aware(timezone.datetime.combine(end_date + timedelta(days=30), timezone.datetime.min.time()))
                
                submission = Submission.objects.create(
                    project=project,
                    downloadable=random.choice(final_templates),
                    deadline=final_deadline,
                    notes="Final project report and documentation",
                    created_by=director,
                    submitted_by=leader,  # Faculty U. Test submits
                    submitted_at=final_deadline - timedelta(days=7),
                    for_product_production=random.choice([True, False]),
                    for_research=random.choice([True, False]),
                    for_extension=random.choice([True, False]),
                    status='APPROVED',  # APPROVED to trigger has_final_submission
                    reviewed_by=coordinator if coordinator else director,
                    reviewed_at=final_deadline - timedelta(days=5),
                    authorized_by=director,
                    authorized_at=final_deadline - timedelta(days=3),
                    updated_by=director,
                )
                
                # Attach placeholder file
                submission.file.name = PLACEHOLDER_PDF_PATH
                submission.save()
            
            project_count += 1
            self.stdout.write(self.style.SUCCESS(f"  ✅ Created COMPLETED project: {project.title} ({estimated_events} events, all completed)"))


        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {project_count} projects for Faculty U. Test!'))
        self.stdout.write(self.style.SUCCESS(f'✅ All projects led by: {faculty_user.get_full_name()} ({faculty_user.email})'))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'   - NOT_STARTED: {not_started_projects} project (future dates)')
        self.stdout.write(f'   - IN_PROGRESS: {in_progress_projects} project (with events and submissions)')
        self.stdout.write(f'   - COMPLETED: {completed_projects} project (all events and submissions done)')
        self.stdout.write(self.style.SUCCESS('\n🎉 All Faculty U. Test projects generated successfully using placeholder URLs!'))
        self.stdout.write(self.style.WARNING('\n💡 Login credentials: faculty@example.com / test1234'))
