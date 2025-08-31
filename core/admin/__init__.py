"""
Admin package - Import tất cả admin classes
"""

# Import tất cả admin classes
from .user_admin import UserProfileAdmin, UserRoleAdmin, UserAdmin
from .auth_admin import LoginHistoryAdmin, PasswordResetAdmin, AccountLockoutAdmin
from .study_admin import CourseAdmin, CourseEnrollmentAdmin, GradeAdmin, NoteAdmin, TagAdmin
from .assignment_admin import AssignmentAdmin, AssignmentFileAdmin, AssignmentSubmissionAdmin, AssignmentGradeAdmin
from .requests_admin import StudentAccountRequestAdmin

__all__ = [
    'UserAdmin', 'UserProfileAdmin', 'UserRoleAdmin',
    'LoginHistoryAdmin', 'PasswordResetAdmin', 'AccountLockoutAdmin',
    'CourseAdmin', 'CourseEnrollmentAdmin', 'GradeAdmin', 'NoteAdmin', 'TagAdmin',
    'AssignmentAdmin', 'AssignmentFileAdmin', 'AssignmentSubmissionAdmin', 'AssignmentGradeAdmin',
    'StudentAccountRequestAdmin',
] 