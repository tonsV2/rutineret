import logging
from django.conf import settings
from urllib.parse import urlencode
import requests

from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import QueryDict

from users.serializers import UserSerializer

User = get_user_model()


@api_view(["GET", "POST"])
@permission_classes([permissions.AllowAny])
def google_oauth_callback(request):
    """Handle Google OAuth callback"""
    try:
        logger = logging.getLogger(__name__)

        # Handle both GET and POST methods
        code = None
        if request.method == "GET":
            code = request.GET.get("code")
        elif request.method == "POST":
            code = request.data.get("code") or request.POST.get("code")

        logger.info(f"Request method: {request.method}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"GET params: {dict(request.GET)}")
        logger.info(f"POST params: {dict(request.POST)}")
        logger.info(f"Extracted code: {code}")

        if not code:
            logger.error("No authorization code found in request!")
            return Response({"error": "Authorization code is required"},status=status.HTTP_400_BAD_REQUEST)

        # Use settings safely
        client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
        client_secret = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["secret"]
        redirect_uri = "http://localhost:8000/api/auth/google/callback/"

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
                return Response(
                    {
                        "error": "OAuth callback failed: Unable to get user ID from Google"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            SocialAccount.objects.create(
                user=user,
                provider="google",
                uid=uid,
                extra_data=user_info,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "Google sign-in successful",
            }
        )

    except Exception as e:
        return Response(
            {"error": f"OAuth callback failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
