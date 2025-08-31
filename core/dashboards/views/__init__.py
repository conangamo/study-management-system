"""
Dashboard views package
"""

from .student import (
    StudentDashboardView, StudentCourseView, StudentCourseDetailView, 
    StudentAssignmentView, StudentGradeView, StudentNoteView
)
from .teacher import (
    TeacherDashboardView, TeacherCourseView, TeacherCourseDetailView,
    TeacherAssignmentView, TeacherGradeView, TeacherStudentView, TeacherGradingView
)
from .admin import (
    AdminDashboardView, AdminUserView, AdminUserDetailView, 
    AdminSystemView, AdminAnalyticsView, AdminImportView
)

__all__ = [
    # Student views
    'StudentDashboardView', 'StudentCourseView', 'StudentCourseDetailView',
    'StudentAssignmentView', 'StudentGradeView', 'StudentNoteView',
    
    # Teacher views
    'TeacherDashboardView', 'TeacherCourseView', 'TeacherCourseDetailView',
    'TeacherAssignmentView', 'TeacherGradeView', 'TeacherStudentView', 'TeacherGradingView',
    
    # Admin views
    'AdminDashboardView', 'AdminUserView', 'AdminUserDetailView', 
    'AdminSystemView', 'AdminAnalyticsView', 'AdminImportView',
] 