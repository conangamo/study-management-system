"""
Teacher Dashboard URLs
"""
from django.urls import path, include
from . import views

app_name = 'teacher'

urlpatterns = [
    # Teacher Dashboard Main
    path('', views.TeacherDashboardView.as_view(), name='dashboard'),
    
    # Course Management
    path('courses/', include([
        path('', views.TeacherCourseListView.as_view(), name='course_list'),
        path('create/', views.TeacherCourseCreateView.as_view(), name='course_create'),
        path('<int:pk>/', views.TeacherCourseDetailView.as_view(), name='course_detail'),
        path('<int:pk>/edit/', views.TeacherCourseUpdateView.as_view(), name='course_edit'),
        path('<int:pk>/delete/', views.TeacherCourseDeleteView.as_view(), name='course_delete'),
        path('<int:pk>/students/', views.TeacherCourseStudentsView.as_view(), name='course_students'),
    ])),
    
    # Assignment Management
    path('assignments/', include([
        path('', views.TeacherAssignmentListView.as_view(), name='assignment_list'),
        path('create/', views.TeacherAssignmentCreateView.as_view(), name='assignment_create'),
        path('<int:pk>/', views.TeacherAssignmentDetailView.as_view(), name='assignment_detail'),
        path('<int:pk>/edit/', views.TeacherAssignmentUpdateView.as_view(), name='assignment_edit'),
        path('<int:pk>/delete/', views.TeacherAssignmentDeleteView.as_view(), name='assignment_delete'),
        path('<int:pk>/submissions/', views.TeacherAssignmentSubmissionsView.as_view(), name='assignment_submissions'),
        path('<int:pk>/grade/', views.TeacherAssignmentGradingView.as_view(), name='assignment_grading'),
    ])),
    
    # Grade Management
    path('grades/', include([
        path('', views.TeacherGradeListView.as_view(), name='grade_list'),
        path('create/', views.TeacherGradeCreateView.as_view(), name='grade_create'),
        path('<int:pk>/edit/', views.TeacherGradeUpdateView.as_view(), name='grade_edit'),
        path('<int:pk>/delete/', views.TeacherGradeDeleteView.as_view(), name='grade_delete'),
        path('statistics/', views.TeacherGradeStatisticsView.as_view(), name='grade_statistics'),
        path('bulk-entry/', views.TeacherBulkGradeEntryView.as_view(), name='bulk_grade_entry'),
    ])),
    
    # Student Management
    path('students/', include([
        path('', views.TeacherStudentListView.as_view(), name='student_list'),
        path('<int:pk>/', views.TeacherStudentDetailView.as_view(), name='student_detail'),
        path('<int:pk>/grades/', views.TeacherStudentGradeView.as_view(), name='student_grades'),
    ])),
] 