from django.urls import path
from .views import login_view, logout_view, register_view, quick_login, role_redirect, home, dashboard, manage_user

urlpatterns = [
    # User Authentication URLs
    path('login/', login_view, name='login'),                   # Login URL
    path('logout/', logout_view, name='logout'),                # Logout URL
    path('register/', register_view, name='register'),          # Registration URL
    path('redirector/', role_redirect, name='role_redirect'),   

    path('home/', home, name='home'),                           # Home (User)
    path('dashboard/', dashboard, name='dashboard'),            # Dashboard (Admin)
    path('users/', manage_user, name='manage_user'),      # Manage User


    path('quick-login/<str:role>/', quick_login, name='quick_login'),       # Quick Login URL (For Testing Purposes)
]