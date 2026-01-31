from rest_framework import permissions
from users.models import Role


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class HasRolePermission(permissions.BasePermission):
    """
    Custom permission to check if user has specific role permission.
    """

    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have all permissions
        if request.user.is_superuser:
            return True

        try:
            user_profile = request.user.profile
            roles = user_profile.roles.all()

            # Check if any role has the required permission
            for role in roles:
                permissions_dict = role.permissions
                if permissions_dict.get(self.required_permission, False):
                    return True

            return False
        except UserProfile.DoesNotExist:
            return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and request.user.is_authenticated and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners or admin users to access objects.
    """

    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_staff:
            return True

        # Owners can access their own objects
        return obj.user == request.user


# Predefined permission classes for common use cases
IsUserManager = HasRolePermission("user_management")
IsContentManager = HasRolePermission("content_management")
IsSystemAdmin = HasRolePermission("system_settings")
