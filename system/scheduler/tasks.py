from django.conf import settings
from system.scheduler.scheduler import (
    publish_scheduled_announcements,
    clear_expired_sessions,
    update_event_statuses,
    update_project_statuses,
    update_user_expert_status,
    send_event_reminders
)


def _task_decorator(func):
    """Use Celery task decorator outside PythonAnywhere mode; otherwise return function unchanged."""
    if getattr(settings, 'PYTHONANYWHERE_VERSION', False):
        return func

    from WBPMISUESO.celery import app
    return app.task(func)


@_task_decorator
def celery_publish_scheduled_announcements():
    publish_scheduled_announcements()


@_task_decorator
def celery_clear_expired_sessions():
    clear_expired_sessions()


@_task_decorator
def celery_update_event_statuses():
    update_event_statuses()


@_task_decorator
def celery_update_project_statuses():
    update_project_statuses()


@_task_decorator
def celery_update_user_expert_status():
    update_user_expert_status()


@_task_decorator
def celery_send_event_reminders():
    send_event_reminders()


# celery -A WBPMISUESO worker --pool=solo 
# celery -A WBPMISUESO beat