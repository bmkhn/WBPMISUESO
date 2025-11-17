"""
Django signals for automatic cache invalidation.
Clears cache whenever models are created, updated, or deleted.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Import all models that should trigger cache clearing

# External
# -- IGNORE --

# Internal
from internal.agenda.models import Agenda
from internal.goals.models import Goal, GoalQualifier
from internal.submissions.models import Submission, SubmissionUpdate

# Shared
from shared.about_us.models import AboutUs
from shared.announcements.models import Announcement
from shared.budget.models import BudgetPool, CollegeBudget, ExternalFunding, BudgetHistory
from shared.downloadables.models import Downloadable
from shared.event_calendar.models import MeetingEvent
from shared.projects.models import SustainableDevelopmentGoal, ProjectDocument, Project, ProjectExpense, ProjectEvaluation, ProjectEvent, ProjectUpdate
from shared.request.models import ClientRequest, RequestUpdate

# System
from system.exports.models import ExportRequest
from system.logs.models import LogEntry
from system.notifications.models import Notification
from system.settings.models import SystemSetting
from system.users.models import Campus, College, User



def clear_site_cache(sender, instance, **kwargs):
    """
    Clear all site cache when any model changes.
    This ensures users always see fresh data.
    """
    try:
        cache.clear()
        model_name = sender.__name__
        action = kwargs.get('created', None)
        
        if action is True:
            logger.info(f"Cache cleared: {model_name} created (ID: {instance.pk})")
        elif action is False:
            logger.info(f"Cache cleared: {model_name} updated (ID: {instance.pk})")
        else:
            logger.info(f"Cache cleared: {model_name} deleted")
    except Exception as e:
        logger.error(f"Error clearing cache for {sender.__name__}: {e}")


# Connect signals for cache clearing
models_to_monitor = [
    Agenda,
    Goal,
    GoalQualifier,
    Submission,
    SubmissionUpdate,
    AboutUs,
    Announcement,
    BudgetPool,
    CollegeBudget,
    ExternalFunding,
    BudgetHistory,
    Downloadable,
    MeetingEvent,
    SustainableDevelopmentGoal,
    ProjectDocument,
    Project,
    ProjectExpense,
    ProjectEvaluation,
    ProjectEvent,
    ProjectUpdate,
    ClientRequest,
    RequestUpdate,
    ExportRequest,
    LogEntry,
    Notification,
    SystemSetting,
    Campus,
    College,
    User
]

for model in models_to_monitor:
    post_save.connect(clear_site_cache, sender=model)
    post_delete.connect(clear_site_cache, sender=model)