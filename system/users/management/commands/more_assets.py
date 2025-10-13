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
		for i in range(10):
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
			self.stdout.write(self.style.SUCCESS(f"Created announcement: {title}"))



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
			degrees = [
				'Bachelor of Science in Mathematics',
				'Bachelor of Science in Biology',
				'Bachelor of Arts in English',
				'Bachelor of Science in Computer Science',
				'Bachelor of Science in Nursing',
				'Bachelor of Science in Civil Engineering',
				'Bachelor of Science in Accountancy',
				'Bachelor of Science in Psychology',
				'Bachelor of Science in Architecture',
				'Bachelor of Science in Tourism Management',
				'Master of Project Management',
				'Master of Public Administration',
				'Master of Business Administration',
				'Master of Environmental Science',
				'Master of Social Work',
				'Master of Education',
				'Master of Engineering',
				'Master of Information Technology',
				'Master of Health Administration',
				'Master of Community Development',
				'Doctor of Philosophy in Education',
				'Doctor of Philosophy in Science',
				'Doctor of Philosophy in Engineering',
				'Doctor of Philosophy in Business',
				'Doctor of Public Administration',
				'Doctor of Medicine',
				'Juris Doctor',
				'Bachelor of Science in Environmental Science',
				'Bachelor of Science in Social Work',
				'Bachelor of Science in Business Administration',
				'Bachelor of Science in Education',
				'Bachelor of Science in Community Development',
			]
			expertise_list = [
				'Mathematics', 'Biology', 'English', 'Computer Science', 'Nursing', 'Civil Engineering', 
				'Accountancy', 'Psychology', 'Architecture', 'Tourism', 'Project Management', 
				'Public Administration', 'Business', 'Environmental Science', 'Social Work', 'Education', 
				'Engineering', 'IT', 'Health Administration', 'Community Development', 'Medical Science', 
				'Law', 'Finance', 'Statistics', 'Physics', 'Chemistry', 'History', 'Political Science', 'Economics', 'Marketing',
				'Human Resources', 'Operations Management', 'Supply Chain', 'Agriculture',
				'Hospitality', 'Arts', 'Communication', 'Media', 'Philosophy', 'Sociology'
			]
			
			for _ in range(20):
				given_name = fake.first_name()
				last_name = fake.last_name()
				email = fake.unique.email()
				username = email.split('@')[0]
				campus = random.choice(campuses)
				college = random.choice(colleges) if colleges else None
				degree = random.choice(degrees)
				expertise = random.choice(expertise_list)
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
					degree=degree,
					expertise=expertise,
				)
		create_user(User.Role.FACULTY)
		create_user(User.Role.IMPLEMENTER)
		self.stdout.write(self.style.SUCCESS("10 faculty and 10 implementer users created."))



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

		for i in range(10):
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
			project = Project.objects.create(
				title=fake.sentence(nb_words=5),
				project_leader=project_leader,
				agenda=agenda,
				project_type=random.choice(['NEEDS_BASED', 'RESEARCH_BASED']),
				estimated_events=random.randint(1, 10),
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
			self.stdout.write(self.style.SUCCESS(f"Created project: {project.title}"))

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
		self.stdout.write(self.style.SUCCESS("10 projects created."))