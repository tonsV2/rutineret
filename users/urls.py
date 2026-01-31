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
    # Roles
    path("roles/", views.RoleListView.as_view(), name="role_list"),
]
