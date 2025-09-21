from django.urls import path
from .views import login_view, logout_view, register_view, quick_login, role_redirect, home, dashboard, forgot_password_view
from .views import registration_client_view, registration_faculty_view, registration_implementer_view, client_verify_view, faculty_verify_view, implementer_verify_view, thank_you_view
from .views import not_authenticated_view, no_permission_view, not_confirmed_view
from .views import manage_user, add_user, user_details_view, edit_user, check_email_view, verify_user, unverify_user, delete_user

urlpatterns = [

    # User Authentication URLs
    path('login/', login_view, name='login'),                   # Login URL
    path('logout/', logout_view, name='logout'),                # Logout URL
    path('register/', register_view, name='register'),          # Registration URL
    path('redirector/', role_redirect, name='role_redirect'),   
    path('forgot-password/1/', forgot_password_view, name='forgot_password'),

    # Registration URLs
    path('check-email/', check_email_view, name='check_email'),
    path('register/client/', registration_client_view, name='registration_client'),
    path('register/client/verify/', client_verify_view, name='verify_client'), 
    path('register/faculty/', registration_faculty_view, name='registration_faculty'),
    path('register/faculty/verify/', faculty_verify_view, name='verify_faculty'),
    path('register/implementer/', registration_implementer_view, name='registration_implementer'),
    path('register/implementer/verify/', implementer_verify_view, name='verify_implementer'),  
    path('register/thank-you/', thank_you_view, name='thank_you'),

    # Error Handling URLs
    path('not-authenticated/', not_authenticated_view, name='not_authenticated'),   # 403 Not Authenticated
    path('no-permission/', no_permission_view, name='no_permission'),               # 403 No Permission
    path('not-confirmed/', not_confirmed_view, name='not_confirmed'),               # 403 Not Confirmed

    path('home/', home, name='home'),                           # Home (User)
    path('dashboard/', dashboard, name='dashboard'),            # Dashboard (Admin)

    path('users/', manage_user, name='manage_user'),                            # Manage User
    path('users/details/<int:id>/', user_details_view, name='user_details'),    # User Details
    path('users/add/', add_user, name='add_user'),                              # Add User
    path('users/edit/<int:id>/', edit_user, name='edit_user'),                  # Edit User
    path('users/delete/<int:id>/', delete_user, name='delete_user'),            # Delete User
    path('users/verify/<int:id>/', verify_user, name='verify_user'),            # Verify User
    path('users/unverify/<int:id>/', unverify_user, name='unverify_user'),      # Unverify User

    path('', role_redirect, name='role_redirect'),              # Default Redirector

    path('quick-login/<str:role>/', quick_login, name='quick_login'),       # Quick Login URL (For Testing Purposes)
]