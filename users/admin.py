from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Role, User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_verified",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "is_verified", "groups")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "phone", "date_of_birth")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "is_public", "created_at")
    list_filter = ("is_public", "roles")
    search_fields = ("user__email", "user__username", "location")
    filter_horizontal = ("roles",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("User Information"), {"fields": ("user",)}),
        (
            _("Profile Details"),
            {"fields": ("bio", "avatar", "location", "website", "is_public")},
        ),
        (_("Roles"), {"fields": ("roles",)}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at",)
