"""
Django admin configuration for core app
"""
from django.contrib import admin
from django.contrib.auth.models import User

# Import models
from .models import (
    UserProfile, UserRole, LoginHistory, PasswordReset, AccountLockout, StudentAccountRequest,
    Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, Tag, Note,
    Document, DocumentCategory, DocumentDownloadLog, DocumentComment
)

# Import admin modules to trigger @admin.register decorators
from .admin import user_admin, auth_admin, study_admin, requests_admin
from .documents import admin as documents_admin

# Import admin classes
from .admin.user_admin import UserAdmin, UserProfileAdmin, UserRoleAdmin
from .admin.auth_admin import LoginHistoryAdmin, PasswordResetAdmin, AccountLockoutAdmin
from .admin.study_admin import (
    CourseAdmin, CourseEnrollmentAdmin, AssignmentAdmin, AssignmentSubmissionAdmin,
    GradeAdmin, TagAdmin, NoteAdmin
)
from .admin.requests_admin import StudentAccountRequestAdmin

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Other models are registered using @admin.register decorators in their respective files

# Customize admin site
admin.site.site_header = "Hệ thống Quản lý Học tập"
admin.site.site_title = "Study Management Admin"
admin.site.index_title = "Quản lý hệ thống" 