from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Group

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

class IsGroupMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a specified group to create content within it.
    Assumes the group_id is available in the request.data or view's kwargs.
    """
    message = "You must be a member of this group to perform this action."

    def has_permission(self, request, view):
        # Allow read operations (GET, HEAD, OPTIONS) for group content, regardless of membership.
        # This means anyone can view group posts (assuming the GroupPostListView allows it).
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations (POST, PUT, PATCH, DELETE)
        if request.user and request.user.is_authenticated:
            group_id = None

            # 1. Try to get group_id from request.data (for StatusPostListCreateView)
            #    This handles the case where the group is part of the POST payload.
            if 'group' in request.data:
                group_id = request.data['group']
            
            # 2. Try to get group_id from view.kwargs (for GroupPostListView if it supported create, or nested URLs)
            #    This handles cases where the group_id is in the URL path, e.g., /groups/{id}/posts/
            elif 'group_id' in view.kwargs:
                group_id = view.kwargs['group_id']

            if group_id:
                try:
                    group = Group.objects.get(pk=group_id)
                    # Check if the requesting user is a member of this group
                    return group.members.filter(pk=request.user.pk).exists()
                except Group.DoesNotExist:
                    # If the group doesn't exist, permission should fail for creation.
                    # The serializer's PrimaryKeyRelatedField will also catch this, but it's good to be explicit.
                    return False 
            else:
                # If 'group_id' is not present in the request data or URL kwargs,
                # it means this is likely a general feed post, not a group-specific one.
                # In this case, this permission class doesn't restrict it, and IsAuthenticated applies.
                return True 
        return False # Not authenticated or no user