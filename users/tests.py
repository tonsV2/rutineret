from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import UserProfile, Role

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }

    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse("users:register")
        response = self.client.post(url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_user_login(self):
        """Test user login endpoint"""
        # Create user first
        User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        url = reverse("users:login")
        response = self.client.post(
            url, {"email": "test@example.com", "password": "testpass123"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_current_user_endpoint(self):
        """Test getting current user info"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.client.force_authenticate(user=user)
        url = reverse("users:current_user")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")


class UserProfileTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        # Profile is created automatically via signals
        self.profile = self.user.profile

    def test_get_profile(self):
        """Test getting user profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse("users:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.profile.id)

    def test_update_profile(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse("users:profile")
        data = {
            "bio": "This is my bio",
            "location": "New York",
            "website": "https://example.com",
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, "This is my bio")
        self.assertEqual(self.profile.location, "New York")


class RoleTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.role = Role.objects.create(
            name="TestRole_" + str(User.objects.count()),
            description="Test role description",
            permissions={"can_test": True},
        )
        self.profile = self.user.profile

    def test_list_roles(self):
        """Test listing roles"""
        self.client.force_authenticate(user=self.user)
        url = reverse("users:role_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], self.role.name)

    def test_assign_roles_to_profile(self):
        """Test assigning roles to user profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse("users:profile")
        data = {"bio": "Updated bio", "role_ids": [self.role.id]}
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertIn(self.role, self.profile.roles.all())
