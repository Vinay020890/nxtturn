from django.contrib import admin
from .models import (
    UserProfile,
    Follow,
    StatusPost,
    ForumCategory,
    Group,
    ForumPost,
    Comment,
    Like # New
) # Import your models from the current app (.)

# Register your models here.

# Basic registration (will show up in admin)
admin.site.register(UserProfile)
admin.site.register(Follow)
admin.site.register(StatusPost)
admin.site.register(ForumCategory) 
admin.site.register(Group)         
admin.site.register(ForumPost)     
admin.site.register(Comment)       
admin.site.register(Like)

# Optional: Customize how models appear in admin (can do later)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'college_name', 'updated_at') # Columns to show in list view
#     search_fields = ('user__username', 'college_name') # Fields to search by

# class FollowAdmin(admin.ModelAdmin):
#     list_display = ('follower', 'following', 'created_at')
#     search_fields = ('follower__username', 'following__username')

# admin.site.register(UserProfile, UserProfileAdmin)
# admin.site.register(Follow, FollowAdmin)
