"""
Django models for core app
"""

# Import all models from sub-modules so Django can discover them
from .user import UserProfile, UserRole
from .authentication import LoginHistory, PasswordReset, AccountLockout
from .study import Course, CourseEnrollment, Grade, Note, Tag, Class
from .requests import StudentAccountRequest
from .academic import AcademicYear, Department, Major, StudentClass, CourseCategory, Curriculum
from .documents import Document, DocumentCategory, DocumentDownloadLog, DocumentComment
from .assignment import Assignment, AssignmentFile, AssignmentSubmission, AssignmentGrade

# Make models available for import
__all__ = [
    'UserProfile', 'UserRole',
    'LoginHistory', 'PasswordReset', 'AccountLockout',
    'Course', 'CourseEnrollment', 'Grade', 'Note', 'Tag', 'Class',
    'StudentAccountRequest',
    'AcademicYear', 'Department', 'Major', 'StudentClass', 'CourseCategory', 'Curriculum',
    'Document', 'DocumentCategory', 'DocumentDownloadLog', 'DocumentComment',
    'Assignment', 'AssignmentFile', 'AssignmentSubmission', 'AssignmentGrade',
] 