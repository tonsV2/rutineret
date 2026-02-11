import logging
import requests
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Role, UserProfile
from .serializers import (
    LoginSerializer,
    RoleSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: UserSerializer},
    description="Register a new user and receive JWT tokens",
    summary="User Registration",
)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "user": UserSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "message": "User registered successfully",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=LoginSerializer,
    responses={200: UserSerializer},
    description="Authenticate user and receive JWT tokens",
    summary="User Login",
)
class CustomLoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Login successful",
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    request=UserProfileSerializer,
    responses={200: UserProfileSerializer},
    description="Get or update user profile information",
    summary="User Profile Management",
)
@extend_schema(
    description="Get or update user profile information",
    summary="User Profile Management",
)
class ProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


@extend_schema(
    description="Get or update current user details",
    summary="User Details Management",
)
class UserDetailView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    description="List all users with optional role filtering",
    summary="User Listing",
)
class UserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_queryset(self):
        queryset = User.objects.select_related("profile").all()
        role = self.request.query_params.get("role")
        if role:
            queryset = queryset.filter(profile__roles__name__iexact=role)
        return queryset


@extend_schema(
    description="List all available roles",
    summary="Role Listing",
)
class RoleListView(ListAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Role.objects.all()


@extend_schema(
    responses={200: UserSerializer},
    description="Get current authenticated user information",
    summary="Current User",
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not user.check_password(old_password):
        return Response(
            {"error": "Invalid old password"}, status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    return Response({"message": "Password changed successfully"})


@extend_schema(
    description="Get Google OAuth authorization URL",
    summary="Google OAuth Initiate",
    responses={
        200: {"type": "object", "properties": {"authorization_url": {"type": "string"}}}
    },
)
@api_view(["GET", "POST"])
@permission_classes([permissions.AllowAny])
def google_oauth_initiate(request):
    """Initiate Google OAuth flow"""
    from allauth.socialaccount.providers.google.views import OAuth2LoginView

    # Build the Google OAuth URL
    from django.conf import settings
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"],
        "scope": " ".join(settings.SOCIALACCOUNT_PROVIDERS["google"]["SCOPE"]),
        "redirect_uri": "http://localhost:8000/api/auth/google/callback/",
        "state": request.GET.get("state", ""),  # CSRF protection
        "access_type": "online",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return Response({"authorization_url": auth_url})


@extend_schema(
    description="Handle Google OAuth callback and redirect to frontend",
    summary="Google OAuth Callback",
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def google_oauth_callback_view(request):
    code = request.GET.get("code")
    error = request.GET.get("error")

    # Build frontend callback URL
    frontend_callback_url = f"{settings.FRONTEND_URL}{settings.OAUTH_CALLBACK_ROUTE}"

    # Handle OAuth errors
    if error:
        error_params = f"?error={error}"
        return redirect(f"{frontend_callback_url}{error_params}")

    if not code:
        error_params = "?error=no_code"
        return redirect(f"{frontend_callback_url}{error_params}")

    try:
        # Use settings safely
        client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
        client_secret = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["secret"]
        redirect_uri = request.build_absolute_uri("/api/auth/google/callback/")

        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        # Get access token from Google
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()

        # Get user info from Google
        userinfo_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={tokens['access_token']}"
        userinfo_response = requests.get(userinfo_url)
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()

        # Get or create user
        email = user_info.get("email")
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": first_name,
                "last_name": last_name,
                "is_verified": True,
            },
        )

        # Create social account link
        if created:
            from allauth.socialaccount.models import SocialAccount

            # Get the user ID from Google OAuth2 v2 userinfo endpoint
            uid = user_info.get("id")
            if not uid:
                error_params = "?error=no_user_id"
                return redirect(f"{frontend_callback_url}{error_params}")

            SocialAccount.objects.create(
                user=user,
                provider="google",
                uid=uid,
                extra_data=user_info,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        user_data = UserSerializer(user).data

        # Include tokens in the redirect URL as URL parameters
        callback_url_with_tokens = f"{frontend_callback_url}?code={code}&access_token={access_token}&refresh_token={refresh_token}"
        return redirect(callback_url_with_tokens)

    except Exception as e:
        # Log the error and redirect with error message
        logger = logging.getLogger(__name__)
        logger.error(f"OAuth callback failed: {str(e)}")
        error_params = f"?error=oauth_failed"
        return redirect(f"{frontend_callback_url}{error_params}")


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def social_accounts(request):
    """Get user's linked social accounts"""
    try:
        from allauth.socialaccount.models import SocialAccount

        social_accounts = SocialAccount.objects.filter(user=request.user)
        accounts_data = []

        for account in social_accounts:
            accounts_data.append(
                {
                    "id": account.id,
                    "provider": account.provider,
                    "uid": account.uid,
                    "extra_data": account.extra_data,
                    "date_joined": account.date_joined,
                }
            )

        return Response({"social_accounts": accounts_data})

    except Exception as e:
        return Response(
            {"error": f"Failed to get social accounts: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def unlink_social_account(request, account_id):
    """Unlink a social account"""
    try:
        from allauth.socialaccount.models import SocialAccount

        account = SocialAccount.objects.get(id=account_id, user=request.user)
        provider = account.provider
        account.delete()

        return Response({"message": f"Successfully unlinked {provider} account"})

    except SocialAccount.DoesNotExist:
        return Response(
            {"error": "Social account not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to unlink account: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
