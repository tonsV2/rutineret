from django.contrib.auth import get_user_model
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
