# community/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Import BaseUserAdmin
from django.contrib.auth import get_user_model                   # Import get_user_model
from django.utils.html import format_html
from django.urls import reverse, NoReverseMatch
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
# --- Import your models ---
from .models import (
    UserProfile, Follow, StatusPost, ForumCategory, Group,
    ForumPost, Comment, Like, Notification, Report  
)
from django.shortcuts import redirect
from django.utils import timezone

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
    
# ... (end of your StatusPostAdmin class)

# ---- ADD THE DETAILED NotificationAdmin CLASS AND REGISTRATION HERE ----
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'recipient_username_link', # Changed to link
        'actor_username_link',     # Changed to link
        'verb', 
        'notification_type', 
        'target_link',             # Changed to link
        'action_object_link',      # Changed to link
        'is_read', 
        'timestamp'
    )
    list_filter = ('is_read', 'notification_type', 'timestamp', 'recipient__username', 'actor__username')
    search_fields = ('recipient__username', 'actor__username', 'verb')
    list_select_related = ('recipient', 'actor', 'target_content_type', 'action_object_content_type')
    date_hierarchy = 'timestamp'

    readonly_fields = (
        'recipient_username_link', 'actor_username_link', 'verb', 'notification_type', 
        'action_object_content_type', 'action_object_object_id', 'action_object_link',
        'target_content_type', 'target_object_object_id', 'target_link',
        'timestamp'
    ) # 'is_read' is left editable

    # In ReportAdmin
    fieldsets = (
        ('Reported Content', {
            'fields': ('content_author_link', 'content_object_link')
        }),
        ('Report Details', {
            'fields': ('reporter_link', 'reason', 'details', 'created_at')
        }),
        ('Moderation', {
            'fields': ('status', 'moderator', 'moderator_notes', 'moderated_at')
        }),
    )

    def _get_admin_obj_url(self, obj_instance):
        if not obj_instance:
            return None
        obj_content_type = ContentType.objects.get_for_model(obj_instance.__class__)
        url_name = f'admin:{obj_content_type.app_label}_{obj_content_type.model}_change'
        try:
            return reverse(url_name, args=(obj_instance.pk,))
        except NoReverseMatch:
            return None

    def recipient_username_link(self, obj):
        if obj.recipient:
            url = self._get_admin_obj_url(obj.recipient)
            if url:
                return format_html('<a href="{}">{}</a>', url, obj.recipient.username)
            return obj.recipient.username
        return "N/A"
    recipient_username_link.short_description = "Recipient"
    recipient_username_link.admin_order_field = 'recipient__username'

    def actor_username_link(self, obj):
        if obj.actor:
            url = self._get_admin_obj_url(obj.actor)
            if url:
                return format_html('<a href="{}">{}</a>', url, obj.actor.username)
            return obj.actor.username
        return "N/A"
    actor_username_link.short_description = "Actor"
    actor_username_link.admin_order_field = 'actor__username'

    def action_object_link(self, obj):
        if obj.action_object:
            url = self._get_admin_obj_url(obj.action_object)
            # Display a snippet of the action object
            obj_str = str(obj.action_object)[:30] + ('...' if len(str(obj.action_object)) > 30 else '')
            if url:
                return format_html('<a href="{}">{} ({})</a>', url, obj_str, obj.action_object_content_type.model)
            return f"{obj_str} ({obj.action_object_content_type.model})"
        return "N/A"
    action_object_link.short_description = 'Action Object'

    def target_link(self, obj):
        if obj.target:
            url = self._get_admin_obj_url(obj.target)
            obj_str = str(obj.target)[:30] + ('...' if len(str(obj.target)) > 30 else '')
            if url:
                return format_html('<a href="{}">{} ({})</a>', url, obj_str, obj.target_content_type.model)
            return f"{obj_str} ({obj.target_content_type.model})"
        return "N/A"
    target_link.short_description = 'Target Object'
# ---- END OF NotificationAdmin CLASS AND REGISTRATION ----

# === PASTE THIS AT THE END of community/admin.py ===

# In community/admin.py

# In community/admin.py

# In community/admin.py

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter_link', 'content_author_link', 'content_object_link', 'reason', 'status', 'created_at', 'moderator')
    list_filter = ('status', 'reason', 'created_at', 'content_type')
    search_fields = ('reporter__username', 'details', 'moderator__username')
    list_editable = ('status',)
    
    # --- We keep these for bulk actions ---
    actions = ['delete_reported_content', 'dismiss_reports']

    # --- Readonly fields now include our new custom display fields ---
    readonly_fields = (
        'reporter_link', 'content_author_link', 'content_type', 'object_id', 
        'content_object_link', 'created_at', 'moderated_at', 'moderator'
    )

    fieldsets = (
        ('Report Details', {
            'fields': ('reporter_link', 'reason', 'details', 'created_at')
        }),
        ('Reported Content', {
            'fields': ('content_author_link', 'content_object_link')
        }),
        ('Moderation', {
            'fields': ('status', 'moderator', 'moderator_notes', 'moderated_at')
        }),
    )

    # --- ACTION METHODS (Unchanged but needed) ---
    @admin.action(description='Delete reported content and mark as "Action Taken"')
    def delete_reported_content(self, request, queryset):
        # ... (this method is unchanged from before)
        items_deleted = 0
        for report in queryset:
            if report.content_object:
                report.content_object.delete()
                items_deleted += 1
        queryset.update(
            status='ACTION_TAKEN', moderator=request.user, moderated_at=timezone.now(),
            moderator_notes=f"Content deleted by {request.user.username} via admin action."
        )
        self.message_user(request, f"{items_deleted} piece(s) of content were successfully deleted.")

    @admin.action(description='Mark selected reports as "Dismissed"')
    def dismiss_reports(self, request, queryset):
        # ... (this method is unchanged from before)
        updated_count = queryset.update(
            status='DISMISSED', moderator=request.user, moderated_at=timezone.now(),
            moderator_notes=f"Report dismissed by {request.user.username} via admin action."
        )
        self.message_user(request, f"{updated_count} report(s) were successfully marked as dismissed.")


    # --- CUSTOM DISPLAY FIELDS WITH LINKS ---
    def get_user_admin_link(self, user_obj):
        if not user_obj: return "N/A"
        url = reverse('admin:auth_user_change', args=[user_obj.pk])
        return format_html('<a href="{}">{}</a>', url, user_obj.username)

    def reporter_link(self, obj):
        # Link to all reports *by* this user
        url = reverse('admin:community_report_changelist') + f'?reporter__id__exact={obj.reporter.id}'
        return format_html('<a href="{}">{} (See all reports)</a>', url, obj.reporter.username)
    reporter_link.short_description = "Reporter"

    def content_author_link(self, obj):
        # Link to all reports *against* content by this author
        if hasattr(obj.content_object, 'author'):
            author = obj.content_object.author
            url = reverse('admin:community_report_changelist') + f'?object_id__in={author.status_posts.values_list("id", flat=True)}'
            return format_html('<a href="{}">{} (See reports for user)</a>', url, author.username)
        return "N/A"
    content_author_link.short_description = "Content Author"

    def content_object_link(self, obj):
        # Link to the reported content itself
        if obj.content_object:
            content_str = str(obj.content_object)
            display_text = (content_str[:75] + '...') if len(content_str) > 75 else content_str
            admin_url = reverse(f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change', args=[obj.object_id])
            return format_html('<a href="{}" target="_blank">{}</a>', admin_url, display_text)
        return "Content not found or has been deleted"
    content_object_link.short_description = 'Reported Content'


    # --- CUSTOM ADMIN ACTIONS ON DETAIL VIEW (The Main Improvement) ---
    def response_change(self, request, obj):
        """
        This is a Django hook that gets called after the 'Save' button is pressed.
        We add our custom logic here.
        """
        if "_delete_content_and_resolve" in request.POST:
            if obj.content_object:
                obj.content_object.delete()
                obj.status = 'ACTION_TAKEN'
                obj.moderator = request.user
                obj.moderated_at = timezone.now()
                obj.moderator_notes = f"Content deleted by {request.user.username} from report detail view."
                obj.save()
                self.message_user(request, "The reported content has been deleted and the report marked as resolved.")
            else:
                self.message_user(request, "Reported content was already deleted. Marked as resolved.", level='warning')
            return redirect("admin:community_report_changelist")

        if "_dismiss_report" in request.POST:
            obj.status = 'DISMISSED'
            obj.moderator = request.user
            obj.moderated_at = timezone.now()
            obj.moderator_notes = f"Report dismissed by {request.user.username} from report detail view."
            obj.save()
            self.message_user(request, "The report has been dismissed.")
            return redirect("admin:community_report_changelist")

        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        This is a Django hook for rendering the detail view page.
        We add extra context to it, which allows us to add custom buttons.
        """
        extra_context = extra_context or {}
        extra_context['show_custom_actions'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)