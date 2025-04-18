from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object (profile) to edit it.
    Assumes the model instance has a `user` attribute.
    Read permissions are allowed to any request (GET, HEAD, OPTIONS).
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the profile.
        # Assumes the model instance has a 'user' attribute.
        # For UserProfile, obj is the UserProfile instance, so obj.user is the owner.
        # --- UPDATED OWNERSHIP CHECK ---
        # Check common attribute names for the owner/author.
        # Add more checks here if your models use different field names.
        if hasattr(obj, 'author'):
            # Check if the object's author is the requesting user
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            # Check if the object's user is the requesting user (e.g., for UserProfile)
            return obj.user == request.user
        # Add more elif checks here if needed for other owner field names

        # If no owner attribute found or doesn't match, deny permission
        return False
        # --- END OF UPDATED CHECK ---