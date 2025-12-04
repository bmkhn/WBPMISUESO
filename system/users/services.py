from django.apps import apps
from django.db.models import Q
from django.conf import settings
from datetime import datetime

def serialize_user_data(user):
    data = {
        'meta': {
            'export_date': str(datetime.now()),
            'version': '1.0',
            'system': 'UESO-PMIS'
        },
        'user_info': {
            'id': user.id,
            'role': user.role,
            'role_display': user.get_role_display(),
            'status': 'Active' if user.is_active else 'Inactive',
            'is_confirmed': user.is_confirmed,
            'joined_at': str(user.date_joined),
        },
        'personal_details': {
            'full_name': user.get_full_name(),
            'email': user.email,
            'contact_no': user.contact_no,
            'sex': user.sex,
            'bio': user.bio,
        },
        'professional_details': {
            'college': user.college.name if user.college else None,
            'campus': user.get_campus_display(),
            'degree': user.degree,
            'expertise': user.expertise,
            'company': user.company,
            'industry': user.industry,
            'is_expert': user.is_expert,
        }
    }

    if apps.is_installed('shared.projects'):
        Project = apps.get_model('projects', 'Project')
        
        led_projects = Project.objects.filter(project_leader=user).select_related('agenda').prefetch_related('sdgs')
        data['projects_led'] = [{
            'id': p.id,
            'title': p.title,
            'status': p.status,
            'type': str(p.project_type),
            'agenda': p.agenda.name if p.agenda else 'N/A',
            'sdgs': [sdg.name for sdg in p.sdgs.all()],
            'beneficiary': p.primary_beneficiary,
            'location': p.primary_location,
            'duration': {
                'start': str(p.start_date),
                'end': str(p.estimated_end_date)
            },
            'financials': {
                'internal_budget': float(p.internal_budget or 0),
                'external_budget': float(p.external_budget or 0),
                'sponsor': p.sponsor_name
            }
        } for p in led_projects]

        member_projects = Project.objects.filter(providers=user).exclude(project_leader=user)
        data['projects_participated'] = [{
            'id': p.id,
            'title': p.title,
            'role': 'Extension Provider',
            'status': p.status,
            'leader': p.project_leader.get_full_name() if p.project_leader else 'N/A'
        } for p in member_projects]

        ProjectExpense = apps.get_model('projects', 'ProjectExpense')
        expenses = ProjectExpense.objects.filter(created_by=user).select_related('project')
        
        data['expenses_logged'] = [{
            'id': e.id,
            'project': e.project.title,
            'amount': float(e.amount),
            'item': e.title,        
            'date': str(e.date_incurred),
        } for e in expenses]

    if apps.is_installed('shared.request'):
        ClientRequest = apps.get_model('request', 'ClientRequest')
        
        requests = ClientRequest.objects.filter(submitted_by=user)
        data['client_requests'] = [{
            'id': r.id,
            'title': r.title,
            'status': r.status,
            'submitted_at': str(r.submitted_at),
            'organization': r.organization,
            'beneficiary': r.primary_beneficiary,
            'review_notes': r.reason if r.status == 'REJECTED' else None
        } for r in requests]

    if apps.is_installed('submissions'):
        Submission = apps.get_model('submissions', 'Submission')
        
        submissions = Submission.objects.filter(submitted_by=user).select_related('project', 'downloadable')
        data['submissions'] = [{
            'id': s.id,
            'project': s.project.title,
            'document_name': s.downloadable.name if s.downloadable else 'Unknown File',
            'status': s.status,
            'submitted_at': str(s.submitted_at),
            'notes': s.notes,
            'revision_count': s.revision_count
        } for s in submissions]

    if apps.is_installed('shared.announcements'):
        Announcement = apps.get_model('announcements', 'Announcement')
        
        announcements = Announcement.objects.filter(published_by=user)
        data['announcements'] = [{
            'id': a.id,
            'title': a.title,
            'is_scheduled': a.is_scheduled,
            'published_at': str(a.published_at),
            'body_snippet': a.body[:100] + '...' if a.body else ''
        } for a in announcements]

    if apps.is_installed('shared.budget'):
        if user.role in ['DIRECTOR', 'VP']:
            CollegeBudget = apps.get_model('budget', 'CollegeBudget')
            budgets_assigned = CollegeBudget.objects.filter(assigned_by=user).select_related('college')
            data['budget_assignments'] = [{
                'college': b.college.name,
                'fiscal_year': b.fiscal_year,
                'amount': float(b.total_assigned),
                'assigned_at': str(b.created_at)
            } for b in budgets_assigned]

    if apps.is_installed('shared.event_calendar'):
        MeetingEvent = apps.get_model('event_calendar', 'MeetingEvent')
        
        events = MeetingEvent.objects.filter(created_by=user)
        data['calendar_events_created'] = [{
            'id': e.id,
            'title': e.title,
            'start': str(e.datetime),   
            'end': str(e.datetime),    
            'type': 'Meeting',          
            'status': e.status
        } for e in events]

    return data