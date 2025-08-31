"""
URL configuration for study_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin (default) - accessible at /django-admin/
    path('django-admin/', admin.site.urls),
    
    # Core app (web interface) - includes custom admin at /admin/
    path('', include('core.urls')),
    
    # Dashboard URLs
    path('dashboard/', include('core.dashboards.urls', namespace='dashboards')),
    
    # API endpoints  
    path('api/', include('core.api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)