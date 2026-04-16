# WBPMISUESO PythonAnywhere Branch Guide

This branch is a lightweight PythonAnywhere-compatible build.

## 1. Install Python dependencies

```
pip install -r requirements.txt
```

## 2. Apply migrations and collect static files

```
python manage.py migrate
python manage.py collectstatic --noinput
```

## 3. Run the web app locally

```
python manage.py runserver
```

## 4. Run scheduled jobs without Celery/Redis

Use this command manually or from PythonAnywhere Scheduled Tasks (cron-style):

```
python manage.py run_all_scheduled_jobs
```

## Notes for this branch

- Redis and Celery are intentionally disabled.
- AI Team Generator is intentionally unavailable and returns:
  This is not available in the pythonanywhere version of the system
- Faker is still available, but generated volume is capped for lighter storage usage.

---

## VS Code Tasks (PythonAnywhere branch)

```
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Django Server",
      "type": "shell",
      "command": "D:/WBPMISUESO/venv/Scripts/Activate.ps1; python manage.py runserver"
    },
    {
      "label": "Run Scheduler Jobs Once",
      "type": "shell",
      "command": "D:/WBPMISUESO/venv/Scripts/Activate.ps1; python manage.py run_all_scheduled_jobs"
    },
    {
      "label": "Start All Services",
      "dependsOn": ["Start Django Server"],
      "dependsOrder": "parallel",
      "type": "shell"
    }
  ]
}
```
