"""
Admin Dashboard URLs
"""
from django.urls import path, include
from . import views

app_name = 'admin'

urlpatterns = [
    # Admin Dashboard Main
    path('', views.AdminDashboardView.as_view(), name='dashboard'),

    # User Management
    path('users/', include([
        path('', views.AdminUserListView.as_view(), name='user_list'),
        path('create/', views.AdminUserCreateView.as_view(), name='user_create'),
        path('<int:pk>/', views.AdminUserDetailView.as_view(), name='user_detail'),
        path('<int:pk>/edit/', views.AdminUserUpdateView.as_view(), name='user_edit'),
        path('<int:pk>/delete/', views.AdminUserDeleteView.as_view(), name='user_delete'),
        path('<int:pk>/toggle-status/', views.AdminToggleUserStatusView.as_view(), name='toggle_user_status'),
        path('<int:pk>/reset-password/', views.AdminResetPasswordView.as_view(), name='reset_password'),
        path('import/', views.AdminUserImportView.as_view(), name='user_import'),
        path('export/', views.AdminUserExportView.as_view(), name='user_export'),
        path('bulk-actions/', views.AdminBulkUserActionsView.as_view(), name='bulk_actions'),
    ])),

    # System Management
    path('system/', include([
        path('', views.AdminSystemManagementView.as_view(), name='system_management'),
        path('courses/', views.AdminCourseListView.as_view(), name='course_list'),
        path('courses/create/', views.AdminCourseCreateView.as_view(), name='course_create'),
        path('courses/<int:pk>/edit/', views.AdminCourseUpdateView.as_view(), name='course_edit'),
        path('courses/<int:pk>/delete/', views.AdminCourseDeleteView.as_view(), name='course_delete'),
        path('assignments/', views.AdminAssignmentManagementView.as_view(), name='assignment_management'),
        path('grades/', views.AdminGradeManagementView.as_view(), name='grade_management'),
        path('database/', views.AdminDatabaseManagementView.as_view(), name='database_management'),
        path('backup/', views.AdminBackupView.as_view(), name='backup'),
        path('logs/', views.AdminLogsView.as_view(), name='logs'),
    ])),

    # Analytics & Reports
    path('analytics/', include([
        path('', views.AdminAnalyticsView.as_view(), name='analytics'),
        path('users/', views.AdminUserAnalyticsView.as_view(), name='user_analytics'),
        path('courses/', views.AdminCourseAnalyticsView.as_view(), name='course_analytics'),
        path('grades/', views.AdminGradeAnalyticsView.as_view(), name='grade_analytics'),
        path('activity/', views.AdminActivityLogView.as_view(), name='activity_log'),
        path('reports/', views.AdminReportsView.as_view(), name='reports'),
        path('export-report/', views.AdminExportReportView.as_view(), name='export_report'),
    ])),

    # API endpoints for AJAX
    path('api/', include([
        path('user-search/', views.AdminUserSearchAPIView.as_view(), name='user_search_api'),
        path('stats/', views.AdminStatsAPIView.as_view(), name='stats_api'),
        path('activity-data/', views.AdminActivityDataAPIView.as_view(), name='activity_data_api'),
    ])),
] 