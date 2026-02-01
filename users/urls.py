from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "users"

urlpatterns = [
    # Authentication
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # User Management
    path("me/", views.current_user, name="current_user"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("user/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    # Password Management
    path("change-password/", views.change_password, name="change_password"),
    # Social Authentication
    path("google/", views.google_oauth_initiate, name="google_oauth_initiate"),
    path(
        "google/callback/",
        views.google_oauth_callback_view,
        name="google_oauth_callback",
    ),
    path("social-accounts/", views.social_accounts, name="social_accounts"),
    path(
        "social-accounts/<int:account_id>/unlink/",
        views.unlink_social_account,
        name="unlink_social_account",
    ),
    # Roles
    path("roles/", views.RoleListView.as_view(), name="role_list"),
]
