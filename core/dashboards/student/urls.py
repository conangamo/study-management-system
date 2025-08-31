"""
Student Dashboard URLs
"""
from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    # Student Dashboard Main
    path('', views.StudentDashboardView.as_view(), name='dashboard'),
    
    # Course Management
    path('courses/', views.StudentCourseListView.as_view(), name='courses'),
    path('courses/<int:pk>/', views.StudentCourseDetailView.as_view(), name='course_detail'),
    path('catalog/', views.StudentCourseCatalogView.as_view(), name='course_catalog'),
    path('courses/<int:pk>/enroll/', views.StudentCourseEnrollView.as_view(), name='course_enroll'),
    
    # Assignment Management
    path('assignments/', views.StudentAssignmentListView.as_view(), name='assignments'),
    path('assignments/course/<int:course_id>/', views.StudentCourseAssignmentListView.as_view(), name='course_assignments'),
    path('assignments/<int:pk>/', views.StudentAssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:pk>/submit/', views.StudentAssignmentSubmitView.as_view(), name='assignment_submit'),
    
    # Grade Management
    path('grades/', views.StudentGradeListView.as_view(), name='grades'),
    
    # Notes Management
    path('notes/', views.StudentNoteListView.as_view(), name='notes'),
    path('notes/create/', views.StudentNoteCreateView.as_view(), name='note_create'),
    path('notes/<int:pk>/', views.StudentNoteDetailView.as_view(), name='note_detail'),
    path('notes/<int:pk>/edit/', views.StudentNoteUpdateView.as_view(), name='note_edit'),
] 