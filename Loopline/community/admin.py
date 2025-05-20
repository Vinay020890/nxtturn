# community/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Import BaseUserAdmin
from django.contrib.auth import get_user_model                   # Import get_user_model
from django.utils.html import format_html
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

# --- ADD THIS BLOCK TO REGISTER UserProfile SEPARATELY ---
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_bio_preview', 'picture_tag') # Added picture_tag
    search_fields = ('user__username', 'bio', 'college_name') # Example search fields
    list_select_related = ('user',) # Optimize user fetch for list_display

    def get_bio_preview(self, obj):
        if obj.bio:
            return obj.bio[:50] + '...' if len(obj.bio) > 50 else obj.bio
        return "---"
    get_bio_preview.short_description = 'Bio Preview'

    # Method to display the picture as an image in the admin list
    def picture_tag(self, obj):
        from django.utils.html import format_html # Import here or at top of file
        if obj.picture and hasattr(obj.picture, 'url'): # Check if picture exists and has a URL
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.picture.url)
        return "No Image"
    picture_tag.short_description = 'Picture'
# --- END OF BLOCK TO ADD ---

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
    list_display = ('id', 'author', 'content_preview', 'image_tag_list', 'video_info_list', 'created_at', 'like_count')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username')
    # Make calculated fields read-only in the detail view
    # readonly_fields = ('like_count',) # like_count might not be directly editable anyway
    readonly_fields = ('image_tag_detail', 'video_player_detail')

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

    def image_tag_list(self, obj):
        if obj.image and hasattr(obj.image, 'url'): 
         return format_html('<img src="{}" style="max-height: 40px; max-width: 50px;" />', obj.image.url)
        return "No Image"
    image_tag_list.short_description = 'Image'

    def image_tag_detail(self, obj):
        if obj.image and hasattr(obj.image, 'url'): 
            return format_html('<div style="margin-top:10px;"><img src="{}" style="max-height: 200px; max-width: 300px;" /></div>', obj.image.url)
        return "No Image Uploaded"
    image_tag_detail.short_description = 'Current Image Preview'
    
    # ---- ADD THESE TWO NEW METHODS FOR VIDEO INFO/PREVIEW ----
    def video_info_list(self, obj):
        if obj.video and hasattr(obj.video, 'url'):
            return format_html('<a href="{}">{}</a>', obj.video.url, obj.video.name.split('/')[-1]) # Display filename as link
        return "No Video"
    video_info_list.short_description = 'Video File'

    def video_player_detail(self, obj): # For the detail/change form display
        if obj.video and hasattr(obj.video, 'url'):
            return format_html(
                '<div style="margin-top:10px;">'
                '<p><a href="{0}">{1}</a></p>'
                '<video controls width="320" height="240">' # Basic HTML5 video player
                '<source src="{0}" type="video/mp4"> Gomenasai! Your browser does not support embedded video.' # Specify type if known, or let browser guess
                '</video>'
                '</div>', obj.video.url, obj.video.name.split('/')[-1]
            )
        return "No Video Uploaded"
    video_player_detail.short_description = 'Current Video Preview'
    # ---- END OF NEW METHODS ----

    # Optional: Define like_count here if not a model property
    # def like_count(self, obj):
    #     return obj.likes.count()
    # like_count.short_description = 'Likes'