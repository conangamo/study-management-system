"""
Custom permissions for API
"""
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission cho phép chỉ owner mới có thể edit/delete
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions cho tất cả requests
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions chỉ cho owner
        return obj.user == request.user


class IsTeacherOrAdmin(BasePermission):
    """
    Permission chỉ cho Teacher hoặc Admin
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.role in ['teacher', 'admin']
        except:
            return False


class IsAdminOnly(BasePermission):
    """Chỉ cho phép admin (hoặc superuser)"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Allow Django superuser
        if request.user.is_superuser:
            return True
        try:
            return hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
        except Exception:
            return False


class IsStudentOnly(BasePermission):
    """
    Permission chỉ cho Student
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.role == 'student'
        except:
            return False


class IsCourseTeacherOrAdmin(BasePermission):
    """
    Permission cho Teacher của course hoặc Admin
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            
            # Admin có full quyền
            if profile.role == 'admin':
                return True
            
            # Teacher chỉ có quyền với course của mình
            if profile.role == 'teacher':
                # Xử lý các model khác nhau
                if hasattr(obj, 'teacher'):  # Course
                    return obj.teacher == request.user
                elif hasattr(obj, 'course'):  # Assignment, Grade, etc
                    return obj.course.teacher == request.user
                
            return False
        except:
            return False


class IsEnrolledStudentOrTeacherOrAdmin(BasePermission):
    """
    Permission cho sinh viên đã đăng ký course, teacher của course, hoặc admin
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            
            # Admin có full quyền
            if profile.role == 'admin':
                return True
            
            # Teacher có quyền với course của mình
            if profile.role == 'teacher':
                if hasattr(obj, 'teacher'):  # Course
                    return obj.teacher == request.user
                elif hasattr(obj, 'course'):  # Assignment, Grade, etc
                    return obj.course.teacher == request.user
            
            # Student chỉ có quyền với course đã đăng ký
            if profile.role == 'student':
                if hasattr(obj, 'students'):  # Course
                    return obj.students.filter(id=request.user.id).exists()
                elif hasattr(obj, 'course'):  # Assignment, Grade, etc
                    return obj.course.students.filter(id=request.user.id).exists()
            
            return False
        except:
            return False


class CanManageAssignment(BasePermission):
    """
    Permission cho việc quản lý assignment
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            
            # Admin có full quyền
            if profile.role == 'admin':
                return True
            
            # Teacher có quyền với assignment của course mình dạy
            if profile.role == 'teacher':
                return obj.course.teacher == request.user
            
            # Student chỉ có quyền xem (không edit/delete)
            if profile.role == 'student':
                if request.method in ['GET', 'HEAD', 'OPTIONS']:
                    return obj.course.students.filter(id=request.user.id).exists()
            
            return False
        except:
            return False


class CanSubmitAssignment(BasePermission):
    """
    Permission cho việc nộp bài
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.role == 'student'
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Student chỉ có thể edit/delete submission của mình
        return obj.student == request.user


class CanGradeAssignment(BasePermission):
    """
    Permission cho việc chấm điểm
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.role in ['teacher', 'admin']
        except:
            return False 