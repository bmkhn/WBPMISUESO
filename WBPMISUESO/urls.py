"""
URL configuration for WBPMISUESO project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken import views as authtoken_views

urlpatterns = [
    # EXTERNAL APPS
    path('home/', include('external.home.urls')),                   # Home

    # INTERNAL APPS
    path('agenda/', include('internal.agenda.urls')),               # Agenda
    path('analytics/', include('internal.analytics.urls')),         # Analytics
    path('dashboard/', include('internal.dashboard.urls')),         # Dashboard
    path('experts/', include('internal.experts.urls')),             # Experts
    path('goals/', include('internal.goals.urls')),                 # Goals
    path('submissions/', include('internal.submissions.urls')),     # Submissions

    # SHARED APPS
    path('about-us/', include('shared.about_us.urls')),             # About Us
    path('announcements/', include('shared.announcements.urls')),   # Announcements
    path('archives/', include('shared.archive.urls')),              # Archives
    path('budget/', include('shared.budget.urls')),                 # Budget
    path('calendar/', include('shared.event_calendar.urls')),       # Calendar
    path('downloadables/', include('shared.downloadables.urls')),   # Downloadables
    path('projects/', include('shared.projects.urls')),             # Projects
    path('requests/', include('shared.request.urls')),              # Requests

    # SYSTEM APPS
    path('logs/', include('system.logs.urls')),                     # Logs
    path('exports/', include('system.exports.urls')),               # Exports
    path('notifications/', include('system.notifications.urls')),   # Notifications
    path('settings/', include('system.settings.urls')),             # Settings
    path('', include('system.users.urls')),                         # Users

    path('api/calendar/', include('shared.event_calendar.api_urls')),
    path('api/requests/', include('shared.request.api_urls')), 
    path('api/get-token/', authtoken_views.obtain_auth_token, name='api_get_token'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)