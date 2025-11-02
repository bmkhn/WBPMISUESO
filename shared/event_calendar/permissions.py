from rest_framework import permissions

class IsEventOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an event to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions (GET, HEAD, OPTIONS) are allowed for any request,
        # so people can see events they are invited to but can't edit them.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions (POST, PUT, PATCH, DELETE) are only allowed
        # if the user is the one who created the event.
        return obj.created_by == request.user