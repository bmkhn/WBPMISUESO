from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django.core.management import call_command
from pytz import timezone as pytz_timezone


def publish_scheduled_announcements():
    """
    Check and publish announcements that are scheduled and past their scheduled time.
    Runs every minute to ensure announcements are published on time.
    """
    from shared.announcements.models import Announcement
    from system.logs.models import LogEntry
    from django.urls import reverse
    
    now = timezone.now()
    
    # Find announcements that are scheduled and past their scheduled time
    scheduled_announcements = Announcement.objects.filter(
        is_scheduled=True,
        scheduled_at__lte=now,
        published_at__isnull=True
    )
    
    count = 0
    for announcement in scheduled_announcements:
        try:
            # Publish the announcement
            announcement.is_scheduled = False
            announcement.published_at = now
            announcement.published_by = announcement.scheduled_by
            
            # Set flag to skip duplicate log entries from signal
            announcement._skip_log = True
            announcement.save()
            
            # Create log entry for notification system
            url = reverse('announcement_details', args=[announcement.id])
            LogEntry.objects.create(
                user=announcement.published_by,
                action='CREATE',
                model='Announcement',
                object_id=announcement.id,
                object_repr=announcement.title,
                details="A new announcement has been published",
                url=url,
                is_notification=True
            )
            
            print(f"✓ Auto-published: {announcement.title}")
            count += 1
            
        except Exception as e:
            print(f"✗ Failed to publish announcement '{announcement.title}': {str(e)}")
    
    if count > 0:
        print(f"✓ Published {count} scheduled announcement(s) at {now.strftime('%Y-%m-%d %H:%M:%S')}")


def clear_expired_sessions():
    """
    Clear expired sessions from database.
    Runs daily to clean up old session data.
    """
    try:
        call_command('clearsessions')
        print(f"✓ Cleared expired sessions at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"✗ Failed to clear sessions: {str(e)}")


def update_event_statuses():
    """
    Automatically update event statuses based on dates.
    - SCHEDULED -> ONGOING when event date is today
    - ONGOING -> COMPLETED when event date is in the past
    
    Runs daily at midnight.
    """
    from shared.event_calendar.models import MeetingEvent
    from shared.projects.models import ProjectEvent
    
    today = timezone.now().date()
    count_ongoing = 0
    count_completed = 0
    
    try:
        # Update MeetingEvent statuses
        # SCHEDULED -> ONGOING (events today)
        meetings_to_ongoing = MeetingEvent.objects.filter(
            status='SCHEDULED',
            datetime__date=today
        )
        
        for meeting in meetings_to_ongoing:
            try:
                meeting.status = 'ONGOING'
                meeting._skip_log = True  # Skip duplicate log entries
                meeting.save()
                count_ongoing += 1
                print(f"✓ Meeting now ongoing: {meeting.title}")
            except Exception as e:
                print(f"✗ Failed to update meeting '{meeting.title}': {str(e)}")
        
        # ONGOING -> COMPLETED (events in the past)
        meetings_to_complete = MeetingEvent.objects.filter(
            status='ONGOING',
            datetime__date__lt=today
        )
        
        for meeting in meetings_to_complete:
            try:
                meeting.status = 'COMPLETED'
                meeting._skip_log = True  # Skip duplicate log entries
                meeting.save()
                count_completed += 1
                print(f"✓ Meeting completed: {meeting.title}")
            except Exception as e:
                print(f"✗ Failed to complete meeting '{meeting.title}': {str(e)}")
        
        # Update ProjectEvent statuses
        # SCHEDULED -> ONGOING (events today)
        project_events_to_ongoing = ProjectEvent.objects.filter(
            status='SCHEDULED',
            datetime__date=today
        )
        
        for event in project_events_to_ongoing:
            try:
                event.status = 'ONGOING'
                event.save()
                count_ongoing += 1
                print(f"✓ Project event now ongoing: {event.title}")
            except Exception as e:
                print(f"✗ Failed to update project event '{event.title}': {str(e)}")
        
        # ONGOING -> COMPLETED (events in the past)
        project_events_to_complete = ProjectEvent.objects.filter(
            status='ONGOING',
            datetime__date__lt=today
        )
        
        for event in project_events_to_complete:
            try:
                event.status = 'COMPLETED'
                event.save()
                count_completed += 1
            except Exception as e:
                pass

        if count_ongoing > 0 or count_completed > 0:
            print(f"✓ Updated event statuses at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}: {count_ongoing} ongoing, {count_completed} completed")
    
    except Exception as e:
        print(f"✗ Failed to update event statuses: {str(e)}")


def update_project_statuses():
    """
    Automatically update project statuses based on dates.
    - NOT_STARTED -> IN_PROGRESS when start_date is reached
    - IN_PROGRESS -> COMPLETED when estimated_end_date is passed (only if no final submission required)
    
    Runs daily at midnight.
    """
    from shared.projects.models import Project
    from system.logs.models import LogEntry
    from django.urls import reverse
    
    now = timezone.now().date()
    count_started = 0
    count_completed = 0
    
    try:
        # Update NOT_STARTED -> IN_PROGRESS
        projects_to_start = Project.objects.filter(
            status='NOT_STARTED',
            start_date__lte=now
        )
        
        for project in projects_to_start:
            try:
                project.status = 'IN_PROGRESS'
                project.save()
                notify_project_status_change(project, 'NOT_STARTED', 'IN_PROGRESS')
                count_started += 1
                print(f"✓ Started project: {project.title}")
            except Exception as e:
                print(f"✗ Failed to start project '{project.title}': {str(e)}")
        
        # Update IN_PROGRESS -> COMPLETED (only if no final submission required)
        projects_to_complete = Project.objects.filter(
            status='IN_PROGRESS',
            estimated_end_date__lt=now,
            has_final_submission=False
        )
        
        for project in projects_to_complete:
            try:
                project.status = 'COMPLETED'
                project.save()
                notify_project_status_change(project, 'IN_PROGRESS', 'COMPLETED')
                count_completed += 1
                print(f"✓ Completed project: {project.title}")
            except Exception as e:
                print(f"✗ Failed to complete project '{project.title}': {str(e)}")
        
        if count_started > 0 or count_completed > 0:
            print(f"✓ Updated project statuses at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}: {count_started} started, {count_completed} completed")
    
    except Exception as e:
        print(f"✗ Failed to update project statuses: {str(e)}")


def update_user_expert_status():
    """
    Update is_expert flag for faculty users based on project involvement.
    - Faculty with at least 1 project as leader or provider -> is_expert = True
    - Faculty with no projects -> is_expert = False
    
    Runs daily at midnight and on startup.
    """
    from system.users.models import User
    from shared.projects.models import Project
    
    count_experts = 0
    count_removed = 0
    
    try:
        # Get all faculty users
        faculty_users = User.objects.filter(role=User.Role.FACULTY)
        
        for user in faculty_users:
            # Check if faculty has at least 1 project (as leader or provider)
            has_projects = Project.objects.filter(
                Q(project_leader=user) | Q(providers=user)
            ).exists()
            
            # Update is_expert status if needed
            if has_projects and not user.is_expert:
                user.is_expert = True
                user.save(update_fields=['is_expert'])
                count_experts += 1

            elif not has_projects and user.is_expert:
                user.is_expert = False
                user.save(update_fields=['is_expert'])
                count_removed += 1
        
        if count_experts > 0 or count_removed > 0:
            print(f"✓ Updated expert statuses at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}: {count_experts} added, {count_removed} removed")
    
    except Exception as e:
        print(f"✗ Failed to update expert statuses: {str(e)}")


def notify_project_status_change(project, old_status, new_status):
    """
    Send notifications to project team and internal users about status change.
    
    Args:
        project: The Project instance
        old_status: Previous status
        new_status: New status
    """
    from system.logs.models import LogEntry
    from django.urls import reverse
    
    try:
        url = reverse('project_profile', args=[project.id])
        status_display = {
            'NOT_STARTED': 'Not Started',
            'IN_PROGRESS': 'In Progress',
            'COMPLETED': 'Completed',
            'ON_HOLD': 'On Hold',
            'CANCELLED': 'Cancelled'
        }
        
        details = f"Project status automatically changed from '{status_display.get(old_status, old_status)}' to '{status_display.get(new_status, new_status)}'"
        
        # Notify project leader
        if project.project_leader:
            LogEntry.objects.create(
                user=project.project_leader,
                action='UPDATE',
                model='Project',
                object_id=project.id,
                object_repr=project.title,
                details=details,
                url=url,
                is_notification=True
            )
        
        # Notify service providers
        for provider in project.service_providers.all():
            LogEntry.objects.create(
                user=provider,
                action='UPDATE',
                model='Project',
                object_id=project.id,
                object_repr=project.title,
                details=details,
                url=url,
                is_notification=True
            )
        
        # Notify internal users (Program Head, Dean, Coordinator) from same college
        if project.college:
            from system.users.models import User
            internal_users = User.objects.filter(
                college=project.college,
                role__in=['PROGRAM_HEAD', 'DEAN', 'COORDINATOR']
            )
            
            for user in internal_users:
                LogEntry.objects.create(
                    user=user,
                    action='UPDATE',
                    model='Project',
                    object_id=project.id,
                    object_repr=project.title,
                    details=details,
                    url=url,
                    is_notification=True
                )
    
    except Exception as e:
        print(f"✗ Failed to send notifications for project '{project.title}': {str(e)}")


def send_event_reminders():
    """
    Send email reminders for upcoming meetings and project events.
    - 3 days before: Send reminder
    - Day of (12:00 AM): Send day-of reminder
    
    Runs daily at midnight.
    """
    from shared.event_calendar.models import MeetingEvent
    from shared.projects.models import ProjectEvent
    from system.utils.email_utils import async_send_event_reminder
    
    now = timezone.now()
    today = now.date()
    three_days_later = today + timedelta(days=3)
    
    reminder_count = 0
    
    try:
        # --- Meeting Event Reminders ---
        
        # 3 days before reminders for meetings
        meetings_3_days = MeetingEvent.objects.filter(
            status='SCHEDULED',
            datetime__date=three_days_later
        ).prefetch_related('participants')
        
        for meeting in meetings_3_days:
            participants = meeting.participants.all()
            participant_emails = [p.email for p in participants if p.email]
            
            if participant_emails:
                async_send_event_reminder(
                    recipient_emails=participant_emails,
                    event_title=meeting.title,
                    event_datetime=meeting.datetime,
                    event_location=meeting.location,
                    event_description=meeting.description,
                    event_type='meeting',
                    days_before=3
                )
                reminder_count += 1
                print(f"✓ Sent 3-day reminder for meeting: {meeting.title}")
        
        # Day-of reminders for meetings
        meetings_today = MeetingEvent.objects.filter(
            status__in=['SCHEDULED', 'ONGOING'],
            datetime__date=today
        ).prefetch_related('participants')
        
        for meeting in meetings_today:
            participants = meeting.participants.all()
            participant_emails = [p.email for p in participants if p.email]
            
            if participant_emails:
                async_send_event_reminder(
                    recipient_emails=participant_emails,
                    event_title=meeting.title,
                    event_datetime=meeting.datetime,
                    event_location=meeting.location,
                    event_description=meeting.description,
                    event_type='meeting',
                    days_before=None
                )
                reminder_count += 1
                print(f"✓ Sent day-of reminder for meeting: {meeting.title}")
        
        # --- Project Event Reminders ---
        
        # 3 days before reminders for project events
        project_events_3_days = ProjectEvent.objects.filter(
            status='SCHEDULED',
            datetime__date=three_days_later,
            placeholder=False
        ).select_related('project__project_leader').prefetch_related('project__providers')
        
        for event in project_events_3_days:
            # Get project team members
            team_emails = []
            if event.project.project_leader and event.project.project_leader.email:
                team_emails.append(event.project.project_leader.email)
            for provider in event.project.providers.all():
                if provider.email:
                    team_emails.append(provider.email)
            
            team_emails = list(set(team_emails))  # Remove duplicates
            
            if team_emails:
                async_send_event_reminder(
                    recipient_emails=team_emails,
                    event_title=event.title,
                    event_datetime=event.datetime,
                    event_location=event.location,
                    event_description=event.description,
                    event_type='activity',
                    days_before=3
                )
                reminder_count += 1
                print(f"✓ Sent 3-day reminder for project event: {event.title}")
        
        # Day-of reminders for project events
        project_events_today = ProjectEvent.objects.filter(
            status__in=['SCHEDULED', 'ONGOING'],
            datetime__date=today,
            placeholder=False
        ).select_related('project__project_leader').prefetch_related('project__providers')
        
        for event in project_events_today:
            # Get project team members
            team_emails = []
            if event.project.project_leader and event.project.project_leader.email:
                team_emails.append(event.project.project_leader.email)
            for provider in event.project.providers.all():
                if provider.email:
                    team_emails.append(provider.email)
            
            team_emails = list(set(team_emails))  # Remove duplicates
            
            if team_emails:
                async_send_event_reminder(
                    recipient_emails=team_emails,
                    event_title=event.title,
                    event_datetime=event.datetime,
                    event_location=event.location,
                    event_description=event.description,
                    event_type='activity',
                    days_before=None
                )
                reminder_count += 1
                print(f"✓ Sent day-of reminder for project event: {event.title}")
        
        if reminder_count > 0:
            print(f"✓ Sent {reminder_count} event reminder(s) at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    except Exception as e:
        print(f"✗ Failed to send event reminders: {str(e)}")