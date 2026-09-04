from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrCrewOwnerReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (request.user and request.user.is_staff)
        )

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        if request.method in SAFE_METHODS:
            return hasattr(request.user, "worker_id") and obj.driver == request.user

        return False
