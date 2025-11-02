# Centralized Scheduler Documentation

## Overview
The centralized scheduler (`system.scheduler`) manages all automated background tasks for the WBPMISUESO system using APScheduler. This consolidates scheduling functionality that was previously scattered across different apps.

## Architecture

### Location
- **App**: `system/scheduler/`
- **Main File**: `system/scheduler/scheduler.py`
- **Configuration**: `system/scheduler/apps.py`

### Key Components
1. **SchedulerConfig (apps.py)**: Django AppConfig that initializes the scheduler on server startup
2. **Scheduler Functions**: Individual task functions that run on schedule
3. **BackgroundScheduler**: APScheduler instance that manages all scheduled jobs

## Scheduled Tasks

### 1. Publish Scheduled Announcements
- **Function**: `publish_scheduled_announcements()`
- **Schedule**: Every 1 minute
- **Purpose**: Auto-publishes announcements that have reached their scheduled time
- **Features**:
  - Checks for announcements with `is_scheduled=True` and `scheduled_at <= now`
  - Sets `published_at` and `published_by` fields
  - Creates log entries for notifications
  - Prevents duplicate logs using `_skip_log` flag

### 2. Clear Expired Sessions
- **Function**: `clear_expired_sessions()`
- **Schedule**: Daily at 3:00 AM
- **Purpose**: Removes expired session data from database
- **Implementation**: Uses Django's built-in `clearsessions` management command

### 3. Update Event Statuses
- **Function**: `update_event_statuses()`
- **Schedule**: Daily at midnight (00:00)
- **Purpose**: Automatically transitions MeetingEvent and ProjectEvent statuses based on dates
- **Logic**:
  - **SCHEDULED → ONGOING**: When `event.datetime.date() == today`
  - **ONGOING → COMPLETED**: When `event.datetime.date() < today`
- **Models Updated**: `MeetingEvent` and `ProjectEvent`
- **Features**:
  - Skips duplicate log entries using `_skip_log` flag for MeetingEvent
  - Updates both meeting and project events
  - Provides console feedback on status changes

### 4. Update Project Statuses
- **Function**: `update_project_statuses()`
- **Schedule**: Daily at midnight (00:00)
- **Purpose**: Automatically transitions project statuses based on dates
- **Logic**:
  - **NOT_STARTED → IN_PROGRESS**: When `start_date <= today`
  - **IN_PROGRESS → COMPLETED**: When `estimated_end_date < today` AND `has_final_submission=False`
- **Notifications**: Sends to project team (leader, providers) and internal users (Program Head, Dean, Coordinator)

## Status Choices

### Event Statuses (MeetingEvent & ProjectEvent)
- **SCHEDULED**: Event is planned for the future
- **ONGOING**: Event is happening today (automatically set at midnight on event date)
- **COMPLETED**: Event has passed (automatically set at midnight after event date)
- **CANCELLED**: Event was cancelled (manual)

### Project Statuses
- **NOT_STARTED**: Project hasn't begun yet
- **IN_PROGRESS**: Project is currently active
- **COMPLETED**: Project has finished
- **ON_HOLD**: Project is temporarily paused
- **CANCELLED**: Project was cancelled

## Notification System

### notify_project_status_change()
Sends notifications when project status is automatically updated:

**Recipients**:
1. Project Leader
2. Service Providers
3. Internal Users from same college (Program Head, Dean, Coordinator)

**Notification Details**:
- Action: UPDATE
- Model: Project
- Details: "Project status automatically changed from '[Old Status]' to '[New Status]'"
- URL: Links to project profile page

## Calendar Integration

The calendar display automatically shows event statuses:

### Visual Indicators
- **Ongoing Badge**: Green badge with "Ongoing" label for events happening today
- **Status Badges in Details**: 
  - SCHEDULED: Blue badge
  - ONGOING: Green badge  
  - COMPLETED: Gray badge
  - CANCELLED: Red badge

### Sidebar Categories
Events are organized in the calendar sidebar:
- **Today**: Events happening today (shows ONGOING badge)
- **Meetings**: Upcoming meeting events
- **Activities**: Upcoming project events
- **Done**: Past events (grayed out, may show status badges)

## Startup Process

### Initialization Flow
1. Django starts server (runserver or gunicorn)
2. `SchedulerConfig.ready()` is called
3. Checks if running in main process (`RUN_MAIN=true`)
4. Checks if running server command (not migrations)
5. Delays scheduler start by 3 seconds using threading.Timer
6. `_start_scheduler()` imports and calls `scheduler.start_scheduler()`
7. BackgroundScheduler is created and jobs are added
8. Scheduler starts in background
9. Immediate announcement check scheduled 5 seconds after startup

### Startup Checks
- **Process Check**: Only runs in main process, not Django reloader
- **Command Check**: Only runs with `runserver` or `gunicorn`, skips migrations
- **Duplicate Prevention**: Uses `scheduler_started` class variable

## Configuration

### Settings.py
```python
INSTALLED_APPS = [
    # ... other apps ...
    'system.scheduler',  # Centralized Scheduler
]
```

### APScheduler Jobs
```python
# Interval job (runs repeatedly)
scheduler.add_job(
    func=publish_scheduled_announcements,
    trigger='interval',
    minutes=1,
    id='publish_announcements',
    replace_existing=True,
    max_instances=1  # Prevents overlapping runs
)

# Cron job (runs at specific time)
scheduler.add_job(
    func=update_event_statuses,
    trigger='cron',
    hour=0,
    minute=0,
    id='update_event_statuses',
    replace_existing=True
)

# One-time job (runs once at specific time)
scheduler.add_job(
    func=publish_scheduled_announcements,
    trigger='date',
    run_date=timezone.now() + timedelta(seconds=5),
    id='publish_announcements_startup',
    replace_existing=True
)
```

## Migration from Announcements Scheduler

### Changes Made
1. **Created** `system/scheduler/` app
2. **Moved** scheduler logic from `shared/announcements/scheduler.py` to `system/scheduler/scheduler.py`
3. **Updated** imports to use absolute paths (e.g., `from shared.announcements.models import Announcement`)
4. **Added** new `update_event_statuses()` function for calendar events
5. **Added** new `update_project_statuses()` function for projects
6. **Removed** scheduler initialization from `shared/announcements/apps.py`
7. **Added** `system.scheduler` to `INSTALLED_APPS`
8. **Updated** MeetingEvent and ProjectEvent models with ONGOING status

### Benefits of Centralization
- **Single Source of Truth**: All scheduled tasks in one location
- **Easier Maintenance**: Add new tasks to one file
- **Better Organization**: System-level functionality in system app
- **Scalability**: Easy to add more scheduled tasks
- **Separation of Concerns**: Apps focus on their domain, not scheduling

## Adding New Scheduled Tasks

### Step 1: Create Task Function
```python
def my_new_task():
    """
    Description of what the task does.
    """
    try:
        # Your task logic here
        print(f"✓ Task completed at {timezone.now()}")
    except Exception as e:
        print(f"✗ Task failed: {str(e)}")
```

### Step 2: Add Job to Scheduler
In `start_scheduler()`:
```python
# For interval-based task
scheduler.add_job(
    my_new_task,
    'interval',
    hours=1,  # or minutes=30, days=1, etc.
    id='my_task_id',
    replace_existing=True
)

# For cron-based task
scheduler.add_job(
    my_new_task,
    'cron',
    hour=9,
    minute=0,
    id='my_task_id',
    replace_existing=True
)
```

### Step 3: Update Print Statement
Add task info to startup message:
```python
print("✓ Centralized Scheduler started:")
print("  - Announcements: checking every minute")
print("  - Session cleanup: daily at 3:00 AM")
print("  - Event status updates: daily at midnight")
print("  - Project status updates: daily at midnight")
print("  - My New Task: every hour")  # Add this
```

## Testing

### Manual Testing
1. Start development server: `python manage.py runserver`
2. Check console for startup message
3. Wait for scheduled times or manually trigger functions in Django shell

### Django Shell Testing
```python
python manage.py shell

from system.scheduler.scheduler import update_event_statuses, update_project_statuses
update_event_statuses()  # Test event status updates
update_project_statuses()  # Test project status updates
```

### Testing Event Status Changes
```python
from shared.event_calendar.models import MeetingEvent
from django.utils import timezone

# Create a test event for today
event = MeetingEvent.objects.create(
    title="Test Event",
    description="Testing status change",
    datetime=timezone.now(),
    status="SCHEDULED"
)

# Run the scheduler function
from system.scheduler.scheduler import update_event_statuses
update_event_statuses()

# Check if status changed to ONGOING
event.refresh_from_db()
print(f"Event status: {event.status}")  # Should print "ONGOING"
```

## Troubleshooting

### Scheduler Not Starting
- Check `RUN_MAIN` environment variable
- Verify running with `runserver` or `gunicorn`
- Check console for error messages
- Ensure APScheduler is installed: `pip install apscheduler`

### Jobs Not Running
- Check scheduler started successfully (console message)
- Verify job ID is unique
- Check `max_instances` setting
- Look for exceptions in task function

### Duplicate Jobs
- Ensure `replace_existing=True` in job configuration
- Use unique job IDs
- Check `scheduler_started` flag in apps.py

### Event Status Not Updating
- Check if events have `datetime` field set correctly
- Verify scheduler is running (check console)
- Test manually in Django shell
- Check for database migration issues

## Database Migrations

After adding ONGOING status to models, create migrations:
```bash
python manage.py makemigrations shared.event_calendar shared.projects
python manage.py migrate
```

**Note**: Existing events with SCHEDULED status will remain SCHEDULED until the scheduler runs at midnight.

## Dependencies
- **APScheduler 3.10.4**: Background job scheduling
- **Django 5.2.6**: Web framework
- **Python 3.x**: Runtime environment

## Related Files
- `system/scheduler/scheduler.py`: Main scheduler logic
- `system/scheduler/apps.py`: Django app configuration
- `WBPMISUESO/settings.py`: App registration
- `shared/projects/models.py`: Project model with status fields
- `shared/event_calendar/models.py`: MeetingEvent model with status fields
- `shared/projects/models.py`: ProjectEvent model with status fields
- `shared/announcements/models.py`: Announcement model
- `system/logs/models.py`: LogEntry for notifications
- `shared/event_calendar/templates/event_calendar/calendar.html`: Calendar UI with status badges

## Future Enhancements
Consider adding:
- Email reminders for upcoming project deadlines
- Automated report generation
- Database backup tasks
- Log cleanup/archiving
- Analytics data aggregation
- Expired downloadable file cleanup
- Notification for events transitioning to ONGOING status
- Automatic event reminder notifications (1 day before, 1 hour before)
- Auto-archive completed events after certain period
