"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # Make sure include is imported
from django.conf import settings             # <-- ADD THIS IMPORT
from django.conf.urls.static import static   # <-- ADD THIS IMPORT

urlpatterns = [
    path('admin/', admin.site.urls),
    # Add the following line for dj-rest-auth endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    # We will also need registration endpoints later
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')), 
     # Add Community App URLs under '/api/' namespace
    path('api/', include('community.urls', namespace='community')), # Add this line
]

# --- ADD THIS BLOCK TO SERVE MEDIA FILES DURING DEVELOPMENT ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# --- END BLOCK ---