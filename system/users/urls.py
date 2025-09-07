from django.urls import path
from .views import login_view, logout_view, register_view, quick_login, role_redirect, home, dashboard, manage_user, forgot_password_view
from .views import registration_client_view, registration_faculty_view, faculty_verify_view, registration_implementer_view, thank_you_view
from external.home.views import home_view

urlpatterns = [
    # User Authentication URLs
    path('login/', login_view, name='login'),                   # Login URL
    path('logout/', logout_view, name='logout'),                # Logout URL
    path('register/', register_view, name='register'),          # Registration URL
    path('redirector/', role_redirect, name='role_redirect'),   
    path('forgot-password/1/', forgot_password_view, name='forgot_password'),

    path('register/client/', registration_client_view, name='registration_client'),

    path('register/faculty/', registration_faculty_view, name='registration_faculty'),
    path('register/faculty/verify/', faculty_verify_view, name='faculty_verify'),

    path('register/implementer/', registration_implementer_view, name='registration_implementer'),

    path('register/thank-you/', thank_you_view, name='thank_you'),


    path('home/', home, name='home'),                           # Home (User)
    path('dashboard/', dashboard, name='dashboard'),            # Dashboard (Admin)
    path('users/', manage_user, name='manage_user'),            # Manage User

    path('', home_view, name='landing_page'),                   # Landing Page (Public)

    path('quick-login/<str:role>/', quick_login, name='quick_login'),       # Quick Login URL (For Testing Purposes)
]