"""
Dashboard URLs - Teacher and Admin dashboards
"""
from django.urls import path, include

app_name = 'dashboards'

urlpatterns = [
    # Student Dashboard
    path('student/', include('core.dashboards.student.urls', namespace='student')),
    
    # Teacher Dashboard
    path('teacher/', include('core.dashboards.teacher.urls', namespace='teacher')),
    
    # Admin Dashboard  
    path('admin/', include('core.dashboards.admin.urls', namespace='admin')),
    
    # Common dashboard views
    path('', include('core.dashboards.common.urls', namespace='common')),
] 