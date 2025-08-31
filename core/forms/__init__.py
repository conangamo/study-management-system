# This file makes core/forms a Python package
# Import all forms to make them available
from .assignment_forms import (
    AssignmentForm, AssignmentFileUploadForm, AssignmentSubmissionForm,
    AssignmentGradeForm, AssignmentSearchForm, AssignmentSubmissionSearchForm
)

from .document_forms import (
    DocumentUploadForm, DocumentEditForm, DocumentSearchForm, 
    DocumentCommentForm, DocumentCategoryForm
)

# Import user account forms
from .user_forms import (
    StudentAccountForm, TeacherAccountForm, BulkStudentAccountForm, 
    UserSearchForm, BulkTeacherAccountForm
)

__all__ = [
    # Assignment forms
    'AssignmentForm', 'AssignmentFileUploadForm', 'AssignmentSubmissionForm',
    'AssignmentGradeForm', 'AssignmentSearchForm', 'AssignmentSubmissionSearchForm',
    
    # Document forms
    'DocumentUploadForm', 'DocumentEditForm', 'DocumentSearchForm', 
    'DocumentCommentForm', 'DocumentCategoryForm',
    
    # User account forms
    'StudentAccountForm', 'TeacherAccountForm', 'BulkStudentAccountForm', 
    'UserSearchForm', 'BulkTeacherAccountForm'
] 