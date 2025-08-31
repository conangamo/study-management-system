"""
Common Dashboard URLs
"""
from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # Dashboard redirect based on user role
    path('', views.DashboardRedirectView.as_view(), name='dashboard_redirect'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/', views.MarkNotificationsReadView.as_view(), name='mark_notifications_read'),
] 