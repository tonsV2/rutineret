from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Role, User, UserProfile


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "bio",
            "avatar",
            "location",
            "website",
            "timezone",
            "roles",
            "role_ids",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        role_ids = validated_data.pop("role_ids", None)

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update roles if provided
        if role_ids is not None:
            roles = Role.objects.filter(id__in=role_ids)
            instance.roles.set(roles)

        return instance


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    social_accounts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "date_of_birth",
            "is_verified",
            "profile",
            "social_accounts",
            "password",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_verified",
            "created_at",
            "updated_at",
            "social_accounts",
        ]

    def get_social_accounts(self, obj):
        """Get user's linked social accounts"""
        try:
            from allauth.socialaccount.models import SocialAccount

            accounts = SocialAccount.objects.filter(user=obj)
            return [
                {
                    "id": account.id,
                    "provider": account.provider,
                    "uid": account.uid,
                    "provider_display_name": account.get_provider().name,
                }
                for account in accounts
            ]
        except:
            return []

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create user profile
        UserProfile.objects.create(user=user)

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "phone",
            "date_of_birth",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        # Profile is created automatically via signals
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), username=email, password=password
            )

            if not user:
                raise serializers.ValidationError("Invalid credentials")

            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")

            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include email and password")


class SocialAccountSerializer(serializers.ModelSerializer):
    """Serializer for social accounts linked to a user"""

    provider = serializers.CharField(read_only=True)
    uid = serializers.CharField(read_only=True)

    class Meta:
        model = None  # Will be set dynamically
        fields = ["id", "provider", "uid"]
        read_only_fields = ["id", "provider", "uid"]
