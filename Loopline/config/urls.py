# C:\Users\Vinay\Project\Loopline\config\urls.py

"""
URL configuration for config project.
... (docstring) ...
"""
from django.contrib import admin
# --- 1. ADD re_path TO THIS IMPORT ---
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

# --- 2. ADD CustomConfirmEmailView TO THIS IMPORT ---
from community.views import ForcefulLogoutView, CustomConfirmEmailView 

urlpatterns = [

    

    path('admin/', admin.site.urls),
    
    path('api/auth/logout/', ForcefulLogoutView.as_view(), name='forceful_rest_logout'),

    # --- 3. ADD THE NEW URL PATTERN HERE ---
    # This URL pattern for email confirmation MUST come BEFORE the default dj_rest_auth URLs are included.
    # It captures the verification key from the URL and passes it to our custom view.
    re_path(
        r'^api/auth/registration/account-confirm-email/(?P<key>[-:\w]+)/$',
        CustomConfirmEmailView.as_view(),
        name='account_confirm_email'
    ),
    # ------------------------------------

    # These are your standard application URLs.
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/', include('community.urls', namespace='community')),
]

# The rest of your file remains unchanged
if settings.DEBUG:
    urlpatterns.append(
        path('api/test/', include('e2e_test_utils.urls'))
    )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)