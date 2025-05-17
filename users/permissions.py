from rest_framework.permissions import BasePermission

class IsFarmer(BasePermission):
    """
    Allows access only to users with role='farmer'.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'farmer'
        )