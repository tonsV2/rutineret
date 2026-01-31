from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.models import Role, UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Create default admin user and roles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", type=str, default="admin@example.com", help="Admin email"
        )
        parser.add_argument(
            "--username", type=str, default="admin", help="Admin username"
        )
        parser.add_argument(
            "--password", type=str, default="admin123", help="Admin password"
        )

    def handle(self, *args, **options):
        email = options["email"]
        username = options["username"]
        password = options["password"]

        # Create superuser
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"User with email {email} already exists")
            )
            admin_user = User.objects.get(email=email)
        else:
            admin_user = User.objects.create_superuser(
                email=email,
                username=username,
                first_name="Admin",
                last_name="User",
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created superuser: {admin_user.email}")
            )

        # Create profile for admin
        profile, created = UserProfile.objects.get_or_create(user=admin_user)
        if created:
            self.stdout.write(self.style.SUCCESS("Created admin profile"))

        # Create default roles
        roles_data = [
            {
                "name": "Admin",
                "description": "Full administrative access",
                "permissions": {
                    "user_management": True,
                    "content_management": True,
                    "system_settings": True,
                },
            },
            {
                "name": "Editor",
                "description": "Content editor with limited permissions",
                "permissions": {
                    "content_management": True,
                    "user_management": False,
                    "system_settings": False,
                },
            },
            {
                "name": "Viewer",
                "description": "Read-only access",
                "permissions": {
                    "content_management": False,
                    "user_management": False,
                    "system_settings": False,
                },
            },
        ]

        created_roles = 0
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data["name"],
                defaults={
                    "description": role_data["description"],
                    "permissions": role_data["permissions"],
                },
            )
            if created:
                created_roles += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created/updated {len(roles_data)} roles ({created_roles} new)"
            )
        )

        # Display credentials
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("ADMIN CREDENTIALS:"))
        self.stdout.write(f"Email: {admin_user.email}")
        self.stdout.write(f"Username: {admin_user.username}")
        self.stdout.write(f"Password: {password}")
        self.stdout.write("=" * 50)
