"""
Utility functions for creating notifications based on log entries
"""
from django.utils import timezone
from django.core.cache import cache
from .models import Notification


def create_notifications_from_log(log_entry):
    """
    Create notifications for relevant users based on a log entry
    Uses bulk_create for better performance when creating multiple notifications
    """
    if not log_entry.is_notification:
        return
    
    # Set notification_date
    log_entry.notification_date = timezone.now()
    log_entry.save(update_fields=['notification_date'])
    
    # Determine recipients based on model type and action
    recipients = get_notification_recipients(log_entry)
    
    # Prepare notifications for bulk creation (skip actor)
    notifications_to_create = [
        Notification(
            recipient=recipient,
            actor=log_entry.user,
            action=log_entry.action,
            model=log_entry.model,
            object_id=log_entry.object_id,
            object_repr=log_entry.object_repr,
            details=log_entry.details,
            url=log_entry.url,
        )
        for recipient in recipients
        if recipient != log_entry.user  # Don't notify the actor about their own action
    ]
    
    # Bulk create all notifications at once (much faster for multiple recipients)
    if notifications_to_create:
        created_notifications = Notification.objects.bulk_create(
            notifications_to_create, 
            batch_size=100
        )
        
        # Invalidate cache for all recipients so they see updated counts
        cache_keys = [f'unread_notif_count_{notif.recipient_id}' for notif in notifications_to_create]
        for cache_key in cache_keys:
            cache.delete(cache_key)
        
        return created_notifications
    
    return []


def get_notification_recipients(log_entry):
    """
    Determine who should receive notifications based on the log entry
    """
    from system.users.models import User
    
    recipients = []
    model = log_entry.model
    action = log_entry.action
    
    # Announcement - notify all confirmed users
    if model == 'Announcement' and action in ['CREATE', 'PUBLISH']:
        recipients = User.objects.filter(is_confirmed=True, is_active=True)
    
    # Project actions
    elif model == 'Project':
        recipients = get_project_notification_recipients(log_entry)
    
    # Submission actions
    elif model == 'Submission':
        recipients = get_submission_notification_recipients(log_entry)
    
    # MeetingEvent actions
    elif model == 'MeetingEvent':
        recipients = get_meeting_event_notification_recipients(log_entry)
    
    # ExportRequest actions
    elif model == 'ExportRequest':
        recipients = get_export_request_notification_recipients(log_entry)
    
    # ClientRequest actions
    elif model == 'ClientRequest':
        recipients = get_client_request_notification_recipients(log_entry)
    
    # User management
    elif model == 'User' and action == 'UPDATE':
        recipients = get_user_update_notification_recipients(log_entry)
    
    return list(set(recipients))  # Remove duplicates


def get_project_notification_recipients(log_entry):
    """
    Get recipients for project notifications
    Director added Faculty & Implementer in a Project → Faculty & Implementer will be notified
    """
    from shared.projects.models import Project
    from system.users.models import User
    
    recipients = []
    
    try:
        project = Project.objects.select_related('project_leader').prefetch_related('providers').get(
            id=log_entry.object_id
        )
        
        # Notify project leader
        if project.project_leader:
            recipients.append(project.project_leader)
        
        # Notify all providers (Faculty & Implementers)
        recipients.extend(project.providers.all())
        
        # For CREATE/UPDATE, also notify supervisors (Coordinator, Dean, Program Head, UESO, Director, VP)
        if log_entry.action in ['CREATE', 'UPDATE']:
            # Get coordinator of the same college as the project leader
            if project.project_leader and project.project_leader.college:
                coordinators = User.objects.filter(
                    role='COORDINATOR',
                    college=project.project_leader.college,
                    is_confirmed=True,
                    is_active=True
                )
                recipients.extend(coordinators)
            
            # Notify UESO, Director, VP
            supervisors = User.objects.filter(
                role__in=['UESO', 'DIRECTOR', 'VP'],
                is_confirmed=True,
                is_active=True
            )
            recipients.extend(supervisors)
        
    except Project.DoesNotExist:
        pass
    
    return recipients


def get_submission_notification_recipients(log_entry):
    """
    Get recipients for submission notifications
    - Director added Submission in Project → Faculty & Implementer will be notified
    - Faculty submitted Submission → Coordinator (of the same college) will be notified
    - Coordinator forwarded to UESO → UESO, Director, VP will be notified
    """
    from internal.submissions.models import Submission
    from system.users.models import User
    
    recipients = []
    
    try:
        submission = Submission.objects.select_related(
            'project__project_leader__college',
            'submitted_by',
            'reviewed_by'
        ).prefetch_related('project__providers').get(id=log_entry.object_id)
        
        project = submission.project
        
        # If submission was created (by Director/Coordinator)
        if log_entry.action == 'CREATE':
            # Notify project leader
            if project.project_leader:
                recipients.append(project.project_leader)
            # Notify all providers
            recipients.extend(project.providers.all())
        
        # If submission was updated (could be faculty submitting, coordinator reviewing, etc.)
        elif log_entry.action == 'UPDATE':
            # Check the status to determine who to notify
            if submission.status == 'SUBMITTED':
                # Faculty submitted → notify coordinator of same college
                if project.project_leader and project.project_leader.college:
                    coordinators = User.objects.filter(
                        role='COORDINATOR',
                        college=project.project_leader.college,
                        is_confirmed=True,
                        is_active=True
                    )
                    recipients.extend(coordinators)
            
            elif submission.status == 'FORWARDED':
                # Coordinator forwarded → notify UESO, Director, VP
                supervisors = User.objects.filter(
                    role__in=['UESO', 'DIRECTOR', 'VP'],
                    is_confirmed=True,
                    is_active=True
                )
                recipients.extend(supervisors)
            
            elif submission.status == 'REVISION_REQUESTED':
                # Coordinator requested revision → notify project leader and providers
                if project.project_leader:
                    recipients.append(project.project_leader)
                recipients.extend(project.providers.all())
            
            elif submission.status in ['APPROVED', 'REJECTED']:
                # UESO/Director/VP approved/rejected → notify project leader, providers, and coordinator
                if project.project_leader:
                    recipients.append(project.project_leader)
                recipients.extend(project.providers.all())
                
                if project.project_leader and project.project_leader.college:
                    coordinators = User.objects.filter(
                        role='COORDINATOR',
                        college=project.project_leader.college,
                        is_confirmed=True,
                        is_active=True
                    )
                    recipients.extend(coordinators)
        
    except Submission.DoesNotExist:
        pass
    
    return recipients


def get_meeting_event_notification_recipients(log_entry):
    """
    Get recipients for meeting event notifications
    Notify all participants
    """
    from shared.event_calendar.models import MeetingEvent
    
    recipients = []
    
    try:
        meeting = MeetingEvent.objects.prefetch_related('participants').get(id=log_entry.object_id)
        # Notify all participants
        recipients.extend(meeting.participants.all())
    except MeetingEvent.DoesNotExist:
        pass
    
    return recipients


def get_export_request_notification_recipients(log_entry):
    """
    Get recipients for export request notifications
    - CREATE: Notify UESO, Director, VP who can approve/reject
    - UPDATE (status change): Notify the requester + UESO, Director, VP
    """
    from system.exports.models import ExportRequest
    from system.users.models import User
    
    recipients = []
    
    try:
        export_request = ExportRequest.objects.select_related('submitted_by').get(
            id=log_entry.object_id
        )
        
        if log_entry.action == 'CREATE':
            # Notify those who can approve (UESO, Director, VP)
            approvers = User.objects.filter(
                role__in=['UESO', 'DIRECTOR', 'VP'],
                is_confirmed=True,
                is_active=True
            )
            recipients.extend(approvers)
        
        elif log_entry.action == 'UPDATE':
            # Notify the requester about status changes (APPROVED/REJECTED)
            if export_request.submitted_by:
                recipients.append(export_request.submitted_by)
            
            # Also notify UESO, Director, VP about the status change
            approvers = User.objects.filter(
                role__in=['UESO', 'DIRECTOR', 'VP'],
                is_confirmed=True,
                is_active=True
            )
            recipients.extend(approvers)
        
    except ExportRequest.DoesNotExist:
        pass
    
    return recipients


def get_client_request_notification_recipients(log_entry):
    """
    Get recipients for client request notifications
    Notify relevant parties based on status changes
    """
    from shared.request.models import ClientRequest
    from system.users.models import User
    
    recipients = []
    
    try:
        client_request = ClientRequest.objects.select_related('submitted_by').get(
            id=log_entry.object_id
        )
        
        if log_entry.action == 'CREATE':
            # New client request → notify UESO, Director, VP
            supervisors = User.objects.filter(
                role__in=['UESO', 'DIRECTOR', 'VP'],
                is_confirmed=True,
                is_active=True
            )
            recipients.extend(supervisors)
        
        elif log_entry.action == 'UPDATE':
            # Status changed → notify the client who submitted
            if client_request.submitted_by:
                recipients.append(client_request.submitted_by)
            
            # Also notify UESO, Director, VP
            supervisors = User.objects.filter(
                role__in=['UESO', 'DIRECTOR', 'VP'],
                is_confirmed=True,
                is_active=True
            )
            recipients.extend(supervisors)
        
    except ClientRequest.DoesNotExist:
        pass
    
    return recipients


def get_user_update_notification_recipients(log_entry):
    """
    Get recipients for user update notifications
    Notify the user who was updated (for role changes, confirmations, etc.)
    """
    from system.users.models import User
    
    recipients = []
    
    try:
        user = User.objects.get(id=log_entry.object_id)
        recipients.append(user)
    except User.DoesNotExist:
        pass
    
    return recipients
