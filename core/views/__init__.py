# This file makes core/views a Python package
# Import all main views
from .main_views import (
    # Basic views
    home, debug_view, simple_home, test_view, test_auth_view, test_student_dashboard,
    login_page, logout_view, profile_page,
    
    # Document views
    document_list, document_upload, document_detail, document_download,
    document_edit, document_delete, document_categories, document_statistics,
    document_my_uploads, document_my_downloads,
    
    # Admin course management
    admin_course_list, admin_course_create, admin_course_edit, admin_course_delete,
    
    # Admin class management  
    admin_class_list, admin_class_create, admin_class_edit, admin_class_delete,
    admin_class_detail, admin_bulk_create_classes,
    
    # API endpoints
    course_list, assignment_list,
    
    # Student course management
    student_course_list, student_course_register, student_course_unregister,
    student_enrolled_courses
)

# Import assignment views
from .assignment_views import (
    assignment_list as assignment_views_list, assignment_create, assignment_detail,
    assignment_submission_list, assignment_file_download
)

__all__ = [
    # Basic views
    'home', 'debug_view', 'simple_home', 'test_view', 'test_auth_view', 'test_student_dashboard',
    'login_page', 'logout_view', 'profile_page',
    
    # Document views
    'document_list', 'document_upload', 'document_detail', 'document_download',
    'document_edit', 'document_delete', 'document_categories', 'document_statistics',
    'document_my_uploads', 'document_my_downloads',
    
    # Admin course management
    'admin_course_list', 'admin_course_create', 'admin_course_edit', 'admin_course_delete',
    
    # Admin class management  
    'admin_class_list', 'admin_class_create', 'admin_class_edit', 'admin_class_delete',
    'admin_class_detail', 'admin_bulk_create_classes',
    
    # API endpoints
    'course_list', 'assignment_list',
    
    # Student course management
    'student_course_list', 'student_course_register', 'student_course_unregister',
    'student_enrolled_courses',
    
    # Assignment views
    'assignment_views_list', 'assignment_create', 'assignment_detail',
    'assignment_submission_list', 'assignment_file_download'
] 