# WBPMISUESO Local Setup Guide

This guide covers installation of system dependencies and running all services for local development on Windows.

## 1. Install Chocolatey (Windows Package Manager)
Chocolatey makes it easy to install Redis and other tools.

With PowerShell, you must ensure `Get-ExecutionPolicy` is not `Restricted`. 

Run `Get-ExecutionPolicy`. If it returns `Restricted`, then run `Set-ExecutionPolicy AllSigned` or `Set-ExecutionPolicy Bypass -Scope Process`.

Now run the following command:

```
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

## 2. Install Redis
After installing Chocolatey, run:

```
choco install redis -y
```

## 3. Python Dependencies
Install all required Python packages:

```
pip install -r requirements.txt
```

## 4. VS Code Tasks: Start All Services
You can start all backend services in separate VS Code terminals using the built-in tasks.

- Open Command Palette (Ctrl+Shift+P)
- Type: `Run Task`
- Select: `Start All Services`

This will launch:
- Redis server
- Celery worker
- Celery beat
- Django development server


---


## VS Code tasks.json Reference

```
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Redis Server",
      "type": "shell",
      "command": "redis-server",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "panel": "dedicated",
        "group": "redis"
      },
      "problemMatcher": []
    },
    {
      "label": "Start Celery Worker",
      "type": "shell",
      "command": "D:/WBPMISUESO/venv/Scripts/Activate.ps1; celery -A WBPMISUESO worker --pool=solo",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "panel": "dedicated",
        "group": "celery"
      },
      "problemMatcher": []
    },
    {
      "label": "Start Celery Beat",
      "type": "shell",
      "command": "D:/WBPMISUESO/venv/Scripts/Activate.ps1; celery -A WBPMISUESO beat",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "panel": "dedicated",
        "group": "celery"
      },
      "problemMatcher": []
    },
    {
      "label": "Start Django Server",
      "type": "shell",
      "command": "D:/WBPMISUESO/venv/Scripts/Activate.ps1; python manage.py runserver",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "panel": "dedicated",
        "group": "django"
      },
      "problemMatcher": []
    },
    {
      "label": "Start All Services",
      "dependsOn": [
        "Start Redis Server",
        "Start Celery Worker",
        "Start Celery Beat",
        "Start Django Server"
      ],
      "dependsOrder": "parallel",
      "type": "shell",
      "presentation": {
        "panel": "dedicated"
      },
      "problemMatcher": []
    }
  ]
}
```
