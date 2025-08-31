"""
API URLs Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views.user_views import (
    CustomTokenObtainPairView, UserListCreateView, UserDetailView,
    CurrentUserView, UserProfileUpdateView, PasswordChangeView,
    UserRoleListCreateView, UserRoleDetailView,
    StudentAccountRequestListCreateView, StudentAccountRequestDetailView,
    approve_student_request, reject_student_request, user_stats
)

from .views.study_views import (
    CourseListCreateView, CourseDetailView, enroll_course, drop_course,
    AssignmentListCreateView, AssignmentDetailView, publish_assignment,
    AssignmentSubmissionListCreateView, AssignmentSubmissionDetailView,
    GradeListCreateView, GradeDetailView,
    TagListCreateView, TagDetailView,
    NoteListCreateView, NoteDetailView,
    course_analytics
)

app_name = 'api'

# Auth URLs
auth_urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='password_change'),
]

# User URLs
user_urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user_list_create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('users/me/', CurrentUserView.as_view(), name='current_user'),
    path('users/me/profile/', UserProfileUpdateView.as_view(), name='user_profile'),
    path('users/stats/', user_stats, name='user_stats'),
    
    # User roles
    path('user-roles/', UserRoleListCreateView.as_view(), name='user_role_list_create'),
    path('user-roles/<int:pk>/', UserRoleDetailView.as_view(), name='user_role_detail'),
    
    # Student account requests
    path('student-requests/', StudentAccountRequestListCreateView.as_view(), name='student_request_list_create'),
    path('student-requests/<int:pk>/', StudentAccountRequestDetailView.as_view(), name='student_request_detail'),
    path('student-requests/<int:pk>/approve/', approve_student_request, name='approve_student_request'),
    path('student-requests/<int:pk>/reject/', reject_student_request, name='reject_student_request'),
]

# Course URLs
course_urlpatterns = [
    path('courses/', CourseListCreateView.as_view(), name='course_list_create'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/enroll/', enroll_course, name='enroll_course'),
    path('courses/<int:pk>/drop/', drop_course, name='drop_course'),
    path('courses/<int:pk>/analytics/', course_analytics, name='course_analytics'),
]

# Assignment URLs
assignment_urlpatterns = [
    path('assignments/', AssignmentListCreateView.as_view(), name='assignment_list_create'),
    path('assignments/<int:pk>/', AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:pk>/publish/', publish_assignment, name='publish_assignment'),
]

# Submission URLs
submission_urlpatterns = [
    path('submissions/', AssignmentSubmissionListCreateView.as_view(), name='submission_list_create'),
    path('submissions/<int:pk>/', AssignmentSubmissionDetailView.as_view(), name='submission_detail'),
]

# Grade URLs
grade_urlpatterns = [
    path('grades/', GradeListCreateView.as_view(), name='grade_list_create'),
    path('grades/<int:pk>/', GradeDetailView.as_view(), name='grade_detail'),
]

# Tag URLs
tag_urlpatterns = [
    path('tags/', TagListCreateView.as_view(), name='tag_list_create'),
    path('tags/<int:pk>/', TagDetailView.as_view(), name='tag_detail'),
]

# Note URLs
note_urlpatterns = [
    path('notes/', NoteListCreateView.as_view(), name='note_list_create'),
    path('notes/<int:pk>/', NoteDetailView.as_view(), name='note_detail'),
]

# Combine all URL patterns
urlpatterns = [
    # Auth
    *auth_urlpatterns,
    
    # Users
    *user_urlpatterns,
    
    # Courses
    *course_urlpatterns,
    
    # Assignments
    *assignment_urlpatterns,
    
    # Submissions
    *submission_urlpatterns,
    
    # Grades
    *grade_urlpatterns,
    
    # Tags
    *tag_urlpatterns,
    
    # Notes
    *note_urlpatterns,
] 