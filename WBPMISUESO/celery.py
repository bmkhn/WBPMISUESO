import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WBPMISUESO.settings')

app = Celery('WBPMISUESO')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.broker_url = 'redis://127.0.0.1:6379/0'  # Or your Railway Redis URL

# --- Celery Startup Hook ---
@app.on_after_configure.connect
def celery_startup(sender, **kwargs):
	print("✓ Celery worker started and ready. Triggering all scheduled tasks once...")
	try:
		from system.scheduler.tasks import (
			celery_publish_scheduled_announcements,
			celery_clear_expired_sessions,
			celery_update_event_statuses,
			celery_update_project_statuses,
			celery_update_user_expert_status,
			celery_send_event_reminders
		)
		celery_publish_scheduled_announcements.delay()
		celery_clear_expired_sessions.delay()
		celery_update_event_statuses.delay()
		celery_update_project_statuses.delay()
		celery_update_user_expert_status.delay()
		celery_send_event_reminders.delay()
		print("✓ All scheduled tasks triggered on startup.")
	except Exception as e:
		print(f"✗ Error triggering startup tasks: {e}")