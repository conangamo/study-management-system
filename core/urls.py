from django.urls import path, include
from core import views
from .auth_views import (
    LoginView, LogoutView, ProfileView, PasswordChangeView,
    PasswordResetRequestView, PasswordResetConfirmView, LoginHistoryView,
    AdminUserListView, AdminUserDetailView, admin_toggle_user_status,
    StudentAccountRequestView, StudentAccountRequestDetailView, StudentAccountRequestActionView
)
from .admin_views import (
    admin_login, admin_logout, admin_dashboard, user_list, create_student_account, create_teacher_account,
    bulk_create_student_accounts, bulk_create_teacher_accounts, toggle_user_status, reset_user_password,
    delete_user, user_search_api, admin_search_classes
)
from django.shortcuts import redirect

def custom_admin_redirect(request):
    """Redirect to custom admin login"""
    return redirect('/custom-admin/login/')

app_name = 'core'

urlpatterns = [
    # Template Views
    path('', views.home, name='home'),
    path('debug/', views.debug_view, name='debug'),  # DEBUG VIEW
    path('simple/', views.simple_home, name='simple_home'),  # Thêm trang simple
    path('test/', views.test_view, name='test'),  # Thêm URL test
    path('test-auth/', views.test_auth_view, name='test_auth'),  # Test auth view
    path('test-student/', views.test_student_dashboard, name='test_student'),  # Debug student dashboard
    path('login/', views.login_page, name='login_page'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_page, name='profile_page'),
    
    # Dashboard URLs
    path('dashboard/', include('core.dashboards.urls')),
    
    # Documents URLs
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/download/', views.document_download, name='document_download'),
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('documents/categories/', views.document_categories, name='document_categories'),
    path('documents/statistics/', views.document_statistics, name='document_statistics'),
    path('documents/my-uploads/', views.document_my_uploads, name='document_my_uploads'),
    path('documents/my-downloads/', views.document_my_downloads, name='document_my_downloads'),
    
    # API Auth Endpoints
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/auth/password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('api/auth/password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('api/auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/login-history/', LoginHistoryView.as_view(), name='login_history'),
    
    # Student Account Management Endpoints
    path('api/student-requests/', StudentAccountRequestView.as_view(), name='student_requests'),
    path('api/student-requests/<int:pk>/', StudentAccountRequestDetailView.as_view(), name='student_request_detail'),
    path('api/student-requests/<int:request_id>/action/', StudentAccountRequestActionView.as_view(), name='student_request_action'),
    
    # Admin API Endpoints
    path('api/admin/users/', AdminUserListView.as_view(), name='admin_users'),
    path('api/admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('api/admin/users/<int:user_id>/toggle-status/', admin_toggle_user_status, name='admin_toggle_user_status'),
    
    # Admin Panel Views - Changed to /custom-admin/ to avoid conflicts
    path('custom-admin/', custom_admin_redirect, name='custom_admin_redirect'),
    path('custom-admin/login/', admin_login, name='admin_login'),
    path('custom-admin/logout/', admin_logout, name='admin_logout'),
    path('custom-admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('custom-admin/users/', user_list, name='admin_user_list'),
    path('custom-admin/users/create-student/', create_student_account, name='create_student_account'),
    path('custom-admin/users/create-teacher/', create_teacher_account, name='create_teacher_account'),
    path('custom-admin/users/bulk-create/', bulk_create_student_accounts, name='bulk_create_student_accounts'),
    path('custom-admin/users/bulk-create-teacher/', bulk_create_teacher_accounts, name='bulk_create_teacher_accounts'),
    path('custom-admin/users/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('custom-admin/users/<int:user_id>/reset-password/', reset_user_password, name='reset_user_password'),
    path('custom-admin/users/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('custom-admin/users/search/', user_search_api, name='user_search_api'),
    path('custom-admin/classes/search/', admin_search_classes, name='admin_search_classes'),
    
    # Admin Course Management URLs - Changed to /custom-admin/ to avoid conflicts
    path('custom-admin/courses/', views.admin_course_list, name='admin_course_list'),
    path('custom-admin/courses/create/', views.admin_course_create, name='admin_course_create'),
    path('custom-admin/courses/<int:pk>/edit/', views.admin_course_edit, name='admin_course_edit'),
    path('custom-admin/courses/<int:pk>/delete/', views.admin_course_delete, name='admin_course_delete'),
    
    # Admin Class Management URLs - Changed to /custom-admin/ to avoid conflicts
    path('custom-admin/classes/', views.admin_class_list, name='admin_class_list'),
    path('custom-admin/classes/create/', views.admin_class_create, name='admin_class_create'),
    path('custom-admin/classes/<int:pk>/edit/', views.admin_class_edit, name='admin_class_edit'),
    path('custom-admin/classes/<int:pk>/delete/', views.admin_class_delete, name='admin_class_delete'),
    path('custom-admin/classes/<int:pk>/detail/', views.admin_class_detail, name='admin_class_detail'),
    path('custom-admin/classes/bulk-create/', views.admin_bulk_create_classes, name='admin_bulk_create_classes'),
    
    # Assignment URLs - Updated for teacher functionality
    path('assignment/', views.assignment_views_list, name='assignment_list'),
    path('assignment/create/', views.assignment_create, name='assignment_create'),
    path('assignment/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignment/<int:assignment_pk>/submissions/', views.assignment_submission_list, name='assignment_submission_list'),
    path('assignment/file/<int:file_pk>/download/', views.assignment_file_download, name='assignment_file_download'),
    
    # Other API Endpoints
    path('api/courses/', views.course_list, name='course_list'),
    path('api/assignments/', views.assignment_list, name='assignment_list'),
    
    # Student Course Management URLs
    path('course/', views.student_course_list, name='student_course_list'),
    path('course/register/<int:course_id>/', views.student_course_register, name='student_course_register'),
    path('course/unregister/<int:course_id>/', views.student_course_unregister, name='student_course_unregister'),
    path('course/enrolled/', views.student_enrolled_courses, name='student_enrolled_courses'),
] 