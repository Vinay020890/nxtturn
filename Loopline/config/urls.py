# C:\Users\Vinay\Project\Loopline\config\urls.py

"""
URL configuration for config project.
... (docstring) ...
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. CLEAN UP THE IMPORTS
# We only need to import the ForcefulLogoutView from the community app now.
from community.views import ForcefulLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This remains the same - our robust logout view.
    path('api/auth/logout/', ForcefulLogoutView.as_view(), name='forceful_rest_logout'),

    # These are your standard application URLs.
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/', include('community.urls', namespace='community')),
]

# 2. THIS IS THE NEW, CLEAN WAY TO ADD ALL DEBUG-ONLY URLS
# It includes the entire e2e_test_utils.urls file under the /api/test/ prefix.
if settings.DEBUG:
    urlpatterns.append(
        path('api/test/', include('e2e_test_utils.urls'))
    )

# 3. YOUR EXISTING MEDIA URLS BLOCK REMAINS THE SAME
# This block correctly serves user-uploaded files during development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)