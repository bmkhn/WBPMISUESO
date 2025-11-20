from WBPMISUESO.celery import app
from system.scheduler.scheduler import (
    publish_scheduled_announcements,
    clear_expired_sessions,
    update_event_statuses,
    update_project_statuses,
    update_user_expert_status,
    send_event_reminders
)

@app.task
def celery_publish_scheduled_announcements():
    publish_scheduled_announcements()

@app.task
def celery_clear_expired_sessions():
    clear_expired_sessions()

@app.task
def celery_update_event_statuses():
    update_event_statuses()

@app.task
def celery_update_project_statuses():
    update_project_statuses()

@app.task
def celery_update_user_expert_status():
    update_user_expert_status()

@app.task
def celery_send_event_reminders():
    send_event_reminders()


# celery -A WBPMISUESO worker --pool=solo 
# celery -A WBPMISUESO beat