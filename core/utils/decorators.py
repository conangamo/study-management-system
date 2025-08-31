"""
Utility decorators for role-based access control
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator để kiểm tra role của user
    
    Args:
        allowed_roles: List hoặc tuple các role được phép
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Bạn cần đăng nhập để truy cập trang này.')
                return redirect('core:login_page')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if hasattr(request.user, 'userprofile'):
                user_role = request.user.userprofile.role
                if user_role in allowed_roles:
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            raise PermissionDenied("Bạn không có quyền truy cập trang này.")
        
        return _wrapped_view
    return decorator


def teacher_required(view_func):
    """Decorator để yêu cầu role teacher"""
    return role_required(['teacher'])(view_func)


def student_required(view_func):
    """Decorator để yêu cầu role student"""
    return role_required(['student'])(view_func)


def admin_required(view_func):
    """Decorator để yêu cầu quyền admin"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Bạn cần đăng nhập để truy cập trang này.')
            return redirect('core:login_page')
        
        if not request.user.is_superuser:
            messages.error(request, 'Bạn cần quyền admin để truy cập trang này.')
            raise PermissionDenied("Bạn cần quyền admin để truy cập trang này.")
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view 