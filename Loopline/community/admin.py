# community/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Import BaseUserAdmin
from django.contrib.auth import get_user_model                   # Import get_user_model
# --- Import your models ---
from .models import (
    UserProfile, Follow, StatusPost, ForumCategory, Group,
    ForumPost, Comment, Like
)

User = get_user_model() # Get the active User model

# --- Define the Inline Admin for UserProfile ---
class UserProfileInline(admin.StackedInline): # Or TabularInline for compact view
    model = UserProfile
    can_delete = False # Don't allow deleting profile from user page
    verbose_name_plural = 'Profile' # Display name in admin
    fk_name = 'user' # Explicitly define the foreign key relationship

# --- Define the Custom User Admin ---
class CustomUserAdmin(BaseUserAdmin):
    # Include the profile inline on the User change page
    inlines = (UserProfileInline, )
    # Keep the default list display or customize as needed
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    # Add profile to select_related if you display profile info in list_display
    list_select_related = ('userprofile',)

    # Override to prevent errors when adding a new user via admin
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# --- Unregister the default User admin and register the custom one ---
try:
    admin.site.unregister(User) # Unregister the standard User admin
except admin.sites.NotRegistered:
    pass # Ignore if it wasn't registered
admin.site.register(User, CustomUserAdmin) # Register User with our custom admin

# --- Register your other models (keep your existing simple registrations) ---
# You DON'T need admin.site.register(UserProfile) anymore as it's inline
admin.site.register(Follow)
admin.site.register(ForumCategory)
admin.site.register(Group)
admin.site.register(ForumPost)
admin.site.register(Comment)
admin.site.register(Like)

# Optional: Add customized admin classes for other models if needed later
@admin.register(StatusPost)
class StatusPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content_preview', 'created_at', 'like_count')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username')
    # Make calculated fields read-only in the detail view
    # readonly_fields = ('like_count',) # like_count might not be directly editable anyway

    def content_preview(self, obj):
        # Shorten content for display
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    

     # --- ADD THIS METHOD to calculate like_count for the admin list ---
    def like_count(self, obj):
        """Calculates the like count for the admin list display."""
        if hasattr(obj, 'likes'): # Check if likes relation exists
            return obj.likes.count()
        return 0
    like_count.short_description = 'Likes' # Sets the column header name
    # --- END ADDED METHOD ---

    # Optional: Define like_count here if not a model property
    # def like_count(self, obj):
    #     return obj.likes.count()
    # like_count.short_description = 'Likes'