from rest_framework.permissions import BasePermission


class IsManagerOrAgent(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return (
            user.groups.filter(name="Manager").exists()
            or user.groups.filter(name="Agent").exists()
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return user.groups.filter(name="Manager").exists()