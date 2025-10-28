import os
import random
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from system.users.models import College
from shared.announcements.models import Announcement
from shared.downloadables.models import Downloadable
from shared.projects.models import Project, ProjectDocument, SustainableDevelopmentGoal
from internal.agenda.models import Agenda



class Command(BaseCommand):
	help = "Add 10 faculty and 10 implementer users with fake data."

	def handle(self, *args, **kwargs):
		User = get_user_model()
		fake = Faker()
		colleges = list(College.objects.all())
		campuses = [c[0] for c in User.Campus.choices]
		password = "test1234"
		director_user = User.objects.filter(role=User.Role.DIRECTOR).first()



		# ADD ANNOUNCEMENTS
		announcement_cover = os.path.join(settings.MEDIA_ROOT, 'announcements', 'PFP.jpg')
		from django.utils import timezone
		import datetime
		number_of_announcements = 10
		for i in range(number_of_announcements):
			title = fake.sentence(nb_words=6)
			body = fake.paragraph(nb_sentences=5)
			cover_photo = None
			if i < 5 and os.path.exists(announcement_cover):
				cover_photo = f'announcements/PFP.jpg'
			# Generate a random aware datetime within this year
			naive_dt = fake.date_time_this_year()
			aware_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
			ann = Announcement.objects.create(
				title=title,
				body=body,
				is_scheduled=False,
				cover_photo=cover_photo,
				published_by=director_user,
				published_at=aware_dt,
			)
		self.stdout.write(self.style.SUCCESS(f"{number_of_announcements} announcements created."))


		# ADD DOWNLOADABLE FILES
		downloadable_files = [
			('Event.docx', 'event'),
			('File.docx', 'file'),
			('Final.docx', 'final'),
		]
		
		for fname, sub_type in downloadable_files:
			file_path = os.path.join(settings.MEDIA_ROOT, 'downloadables', 'files', fname)
			if os.path.exists(file_path):
				if not Downloadable.objects.filter(file=f'downloadables/files/{fname}').exists():
					d = Downloadable.objects.create(
						file=f'downloadables/files/{fname}',
						uploaded_by=director_user,
						status='published',
						is_submission_template=True,
						submission_type=sub_type,
					)
					self.stdout.write(self.style.SUCCESS(f"Added Downloadable: {fname} ({sub_type})"))
				else:
					self.stdout.write(self.style.WARNING(f"Downloadable already exists: {fname}"))
			else:
				self.stdout.write(self.style.WARNING(f"File not found in media: {fname}"))



		# ADD USERS
		def create_user(role):
			# Realistic degree to expertise mappings
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
			
			for _ in range(50):
				given_name = fake.first_name()
				last_name = fake.last_name()
				email = fake.unique.email()
				base_username = email.split('@')[0]
				username = base_username
				campus = random.choice(campuses)
				college = random.choice(colleges) if colleges else None

				# Pick a realistic degree-expertise pair
				degree, expertise = random.choice(degree_expertise_pairs)

				# Ensure username is unique
				suffix = 1
				while User.objects.filter(username=username).exists():
					username = f"{base_username}{suffix}"
					suffix += 1

				user = User.objects.create_user(
					username=username,
					email=email,
					password=password,
					given_name=given_name,
					middle_initial=fake.random_letter().upper(),
					last_name=last_name,
					sex=User.Sex.MALE if random.random() < 0.5 else User.Sex.FEMALE,
					contact_no=fake.phone_number(),
					campus=campus,
					college=college,
					role=role,
					is_confirmed=True,
					is_expert=True,
					bio=fake.paragraph(nb_sentences=3),
					degree=degree,
					expertise=expertise,
					created_by=director_user,
					created_at=timezone.now()
				)
		create_user(User.Role.FACULTY)
		create_user(User.Role.IMPLEMENTER)
		self.stdout.write(self.style.SUCCESS("50 faculty and 50 implementer users created with realistic degree-expertise pairings."))



		# ADD PROJECTS
		faculty_users = list(User.objects.filter(role=User.Role.FACULTY))
		implementer_users = list(User.objects.filter(role=User.Role.IMPLEMENTER))
		all_providers = faculty_users + implementer_users
		director_user = User.objects.filter(role=User.Role.DIRECTOR).first()
		agendas = list(Agenda.objects.all())
		sdgs = list(SustainableDevelopmentGoal.objects.all())
		file_docx_path = os.path.join(settings.MEDIA_ROOT, 'downloadables', 'files', 'File.docx')

		now = timezone.now().date()
		quarter_months = [1, 4, 7, 10]
		def next_quarter_start(date):
			# Returns the first day of the next quarter after the given date
			month = ((date.month - 1) // 3 + 1) * 3 + 1
			year = date.year
			if month > 12:
				month = 1
				year += 1
			return datetime.date(year, month, 1)

		number_of_projects = 20
		for i in range(number_of_projects):
			# Random project leader (faculty)
			project_leader = random.choice(faculty_users) if faculty_users else None
			# Providers: 2-4 random from faculty+implementer
			providers = random.sample(all_providers, min(len(all_providers), random.randint(2, 4))) if all_providers else []
			agenda = random.choice(agendas) if agendas else None
			project_sdgs = random.sample(sdgs, min(len(sdgs), random.randint(1, 3))) if sdgs else []
			# Random start date within the last year
			start_date = fake.date_between(start_date='-1y', end_date='today')
			# Estimated end date 1-6 months after start
			estimated_end_date = start_date + datetime.timedelta(days=random.randint(30, 180))
			# Status: first 5 completed, rest random
			status = 'COMPLETED' if i < 5 else random.choice(['NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'CANCELLED'])

			# Create Project first (without proposal/additional docs)
			estimated_events = random.randint(1, 10)
			project = Project.objects.create(
				title=fake.sentence(nb_words=5),
				project_leader=project_leader,
				agenda=agenda,
				project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
				estimated_events=estimated_events,
				estimated_trainees=random.randint(10, 100),
				primary_beneficiary=fake.company(),
				primary_location=fake.city(),
				logistics_type=random.choice(['BOTH', 'EXTERNAL', 'INTERNAL']),
				internal_budget=random.uniform(10000, 100000),
				external_budget=random.uniform(10000, 100000),
				sponsor_name=fake.company(),
				start_date=start_date,
				estimated_end_date=estimated_end_date,
				created_by=director_user,
				status=status,
			)
			# Create ProjectEvents for this project
			from shared.projects.models import ProjectEvent, ProjectEvaluation
			for eidx in range(estimated_events):
				ProjectEvent.objects.create(
					project=project,
					title=f"Event {eidx+1}",
					description="Description Here",
					datetime=None,
					location="",
					created_at=timezone.now(),
					created_by=director_user,
					image=None,
					placeholder=True
				)
			# Now create proposal and additional docs with project FK
			proposal_doc = None
			additional_docs = []
			if os.path.exists(file_docx_path):
				proposal_doc = ProjectDocument.objects.create(
					project=project,
					file=f'downloadables/files/File.docx',
					document_type='PROPOSAL',
					description='Project proposal document',
				)
				for j in range(2):
					additional_doc = ProjectDocument.objects.create(
						project=project,
						file=f'downloadables/files/File.docx',
						document_type='ADDITIONAL',
						description=f'Additional document {j+1}',
					)
					additional_docs.append(additional_doc)
				# Set proposal_document and additional_documents
				project.proposal_document = proposal_doc
				project.save(update_fields=['proposal_document'])
				project.additional_documents.set(additional_docs)
			project.providers.set(providers)
			project.sdgs.set(project_sdgs)
			project.save()
			# Add at least 5 ProjectEvaluation with ratings 1-5, evaluated_by=director_user
			for rating in range(1, 6):
				ProjectEvaluation.objects.create(
					project=project,
					evaluated_by=director_user,
					created_at=timezone.now().date(),
					comment=f"Auto-generated evaluation with rating {rating}",
					rating=rating
				)

			# Mark users as expert if project has passed a quarter
			next_q = next_quarter_start(project.start_date)
			if now >= next_q:
				# Project has passed a quarter, mark leader and providers as expert
				if project_leader:
					project_leader.is_expert = True
					project_leader.save(update_fields=['is_expert'])
				for user in providers:
					user.is_expert = True
					user.save(update_fields=['is_expert'])
		self.stdout.write(self.style.SUCCESS(f"{number_of_projects} projects created."))


		# ADD TEST PROJECT
		leader = User.objects.filter(given_name='Faculty', last_name='User').first()
		if leader:
			agenda = Agenda.objects.first()
			sdgs = list(SustainableDevelopmentGoal.objects.all())
			project = Project.objects.create(
				title='Test',
				project_leader=leader,
				agenda=agenda,
				project_type='NEEDS_BASED',
				estimated_events=5,
				estimated_trainees=30,
				primary_beneficiary='Test Beneficiary',
				primary_location='Test City',
				logistics_type='BOTH',
				internal_budget=10000,
				external_budget=5000,
				sponsor_name='Test Sponsor',
				start_date=timezone.now().date(),
				estimated_end_date=timezone.now().date() + datetime.timedelta(days=90),
				created_by=director_user,
				status='NOT_STARTED',
			)
			# Add ProjectEvents for test project
			from shared.projects.models import ProjectEvent
			for eidx in range(project.estimated_events):
				ProjectEvent.objects.create(
					project=project,
					title=f"Event {eidx+1}",
					description="Description Here",
					datetime=None,
					location="",
					created_at=timezone.now(),
					created_by=leader,
					updated_at=timezone.now(),
					updated_by=leader,
					image=None,
					placeholder=True
				)
			if sdgs:
				project.sdgs.set(sdgs[:2])
			# Add proposal_document and additional_documents
			file_path = 'downloadables/files/File.docx'
			proposal_doc = ProjectDocument.objects.create(
				project=project,
				file=file_path,
				document_type='PROPOSAL',
				description='Test proposal document',
			)
			additional_docs = []
			for i in range(2):
				additional_doc = ProjectDocument.objects.create(
					project=project,
					file=file_path,
					document_type='ADDITIONAL',
					description=f'Test additional document {i+1}',
				)
				additional_docs.append(additional_doc)
			project.proposal_document = proposal_doc
			project.save(update_fields=['proposal_document'])
			project.additional_documents.set(additional_docs)
			self.stdout.write(self.style.SUCCESS(f"Created project: {project.title} (Leader: {leader.get_full_name()}"))
			
			# ADD 5 COMPLETED PROJECTS FOR FACULTY T. USER
			completed_project_titles = [
				'Community Environmental Awareness Program',
				'Digital Literacy Training for Rural Schools',
				'Sustainable Agriculture Workshop Series',
				'Youth Leadership Development Initiative',
				'Health and Wellness Community Outreach'
			]
			
			for idx, title in enumerate(completed_project_titles):
				# Set dates in the past
				start_date = timezone.now().date() - datetime.timedelta(days=random.randint(180, 365))
				end_date = start_date + datetime.timedelta(days=random.randint(60, 120))
				
				completed_proj = Project.objects.create(
					title=title,
					project_leader=leader,
					agenda=agenda,
					project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
					estimated_events=random.randint(3, 7),
					estimated_trainees=random.randint(20, 80),
					primary_beneficiary=fake.company(),
					primary_location=fake.city(),
					logistics_type=random.choice(['BOTH', 'EXTERNAL', 'INTERNAL']),
					internal_budget=random.uniform(15000, 80000),
					external_budget=random.uniform(10000, 60000),
					sponsor_name=fake.company(),
					start_date=start_date,
					estimated_end_date=end_date,
					created_by=director_user,
					status='COMPLETED',
				)
				
				# Add ProjectEvents for completed project
				for eidx in range(completed_proj.estimated_events):
					ProjectEvent.objects.create(
						project=completed_proj,
						title=f"Event {eidx+1}",
						description=fake.sentence(nb_words=10),
						datetime=timezone.make_aware(
							datetime.datetime.combine(
								start_date + datetime.timedelta(days=random.randint(10, 60)),
								datetime.time(hour=random.randint(9, 16), minute=0)
							)
						),
						location=fake.city(),
						created_at=timezone.now(),
						created_by=leader,
						updated_at=timezone.now(),
						updated_by=leader,
						image=None,
						placeholder=False
					)
				
				if sdgs:
					completed_proj.sdgs.set(random.sample(sdgs, min(len(sdgs), random.randint(2, 4))))
				
				# Add proposal and additional documents
				proposal_doc_completed = ProjectDocument.objects.create(
					project=completed_proj,
					file=file_path,
					document_type='PROPOSAL',
					description=f'{title} proposal document',
				)
				additional_docs_completed = []
				for i in range(random.randint(1, 3)):
					additional_doc_completed = ProjectDocument.objects.create(
						project=completed_proj,
						file=file_path,
						document_type='ADDITIONAL',
						description=f'Additional document {i+1}',
					)
					additional_docs_completed.append(additional_doc_completed)
				completed_proj.proposal_document = proposal_doc_completed
				completed_proj.save(update_fields=['proposal_document'])
				completed_proj.additional_documents.set(additional_docs_completed)
				
				self.stdout.write(self.style.SUCCESS(f"Created completed project {idx+1}/5: {title}"))
			
			self.stdout.write(self.style.SUCCESS(f"Added 5 completed projects for Faculty T. User"))
		else:
			self.stdout.write(self.style.WARNING("Faculty T. User not found. Test project not created."))


