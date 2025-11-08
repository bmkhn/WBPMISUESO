from django.http import HttpResponse
from django.urls import path
from .views import login_view, logout_view, register_view, quick_login, role_redirect, home, dashboard, forgot_password_view
from .views import verify_login_2fa_view, send_password_reset_code_view, verify_reset_code_view, reset_password_view
from .views import session_test_view
from .views import registration_unified_view, verify_unified_view, thank_you_view, send_verification_code_view
from .views import not_authenticated_view, no_permission_view, not_confirmed_view
from .views import manage_user, add_user, user_details_view, edit_user, check_email_view, verify_user, unverify_user, delete_user
from .views import profile_view, update_bio, update_profile_picture
from .views import health_check

urlpatterns = [
    path('session-test/', session_test_view, name='session_test'),  # Session Test Page

    # User Authentication URLs
    path('login/', login_view, name='login'),                   # Login URL
    path('verify-login-2fa/', verify_login_2fa_view, name='verify_login_2fa'),  # Login 2FA Verification
    path('logout/', logout_view, name='logout'),                # Logout URL
    path('register/', register_view, name='register'),          # Registration URL
    path('redirector/', role_redirect, name='role_redirect'),   
    path('forgot-password/1/', forgot_password_view, name='forgot_password'),
    path('send-password-reset-code/', send_password_reset_code_view, name='send_password_reset_code'),
    path('verify-reset-code/', verify_reset_code_view, name='verify_reset_code'),
    path('reset-password/', reset_password_view, name='reset_password'),

    # New Unified Registration URLs
    path('register/<str:role>/', registration_unified_view, name='registration_unified'),
    path('register/verify/', verify_unified_view, name='verify_unified'),
    path('register/thank-you/', thank_you_view, name='thank_you'),
    path('send-verification-code/', send_verification_code_view, name='send_verification_code'),

    # Email Check
    path('check-email/', check_email_view, name='check_email'),

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

    # User Profile URLs
    path('profile/', profile_view, name='profile'),                             # User Profile
    path('profile/<int:id>/', profile_view, name='user_profile'),               # View Any User Profile
    path('profile/update-bio/', update_bio, name='update_bio'),                 # Update Bio
    path('profile/update-picture/', update_profile_picture, name='update_profile_picture'),  # Update Profile Picture

    path('', role_redirect, name='role_redirect'),              # Default Redirector

    path('quick-login/<str:role>/', quick_login, name='quick_login'),       # Quick Login URL (For Testing Purposes)

    path('health/', health_check, name='health_check'),
]