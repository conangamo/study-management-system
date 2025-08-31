"""
Django models for core app
"""

# Import all models from sub-modules so Django can discover them
from .models.user import UserProfile, UserRole
from .models.authentication import LoginHistory, PasswordReset, AccountLockout
from .models.study import Course, CourseEnrollment, Grade, Note, Tag
from .models.assignment import Assignment, AssignmentSubmission
from .models.requests import StudentAccountRequest

# Import documents models
from .documents.models import Document, DocumentCategory, DocumentDownloadLog, DocumentComment

# Make models available for import
__all__ = [
    'UserProfile', 'UserRole',
    'LoginHistory', 'PasswordReset', 'AccountLockout',
    'Course', 'CourseEnrollment', 'Assignment', 'AssignmentSubmission', 'Grade', 'Note', 'Tag',
    'Document', 'DocumentCategory', 'DocumentDownloadLog', 'DocumentComment',
    'StudentAccountRequest',
] 