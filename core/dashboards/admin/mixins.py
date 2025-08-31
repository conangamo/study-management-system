"""
Admin Dashboard Mixins
- Permission checks
- Common functionality
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure user is logged in and has admin role
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has admin profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Tài khoản chưa được thiết lập profile.')
            return redirect('core:profile')
        
        if not request.user.profile.is_admin:
            messages.error(request, 'Bạn không có quyền truy cập vào trang này.')
            raise PermissionDenied("Chỉ quản trị viên mới có thể truy cập trang này.")
        
        return super().dispatch(request, *args, **kwargs)


class AdminSuccessMessageMixin:
    """
    Mixin to add success messages for admin actions
    """
    success_message_create = "Đã tạo thành công!"
    success_message_update = "Đã cập nhật thành công!"
    success_message_delete = "Đã xóa thành công!"
    
    def form_valid(self, form):
        """Add success message on form save"""
        response = super().form_valid(form)
        
        if hasattr(self, 'success_message_create') and not form.instance.pk:
            messages.success(self.request, self.success_message_create)
        elif hasattr(self, 'success_message_update'):
            messages.success(self.request, self.success_message_update)
            
        return response
    
    def delete(self, request, *args, **kwargs):
        """Add success message on delete"""
        response = super().delete(request, *args, **kwargs)
        if hasattr(self, 'success_message_delete'):
            messages.success(request, self.success_message_delete)
        return response


class AdminContextMixin:
    """
    Mixin to add common context data for admin views
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add admin info
        context['admin'] = self.request.user
        context['admin_profile'] = self.request.user.profile
        
        # Add navigation info
        context['dashboard_type'] = 'admin'
        
        return context


class AdminAuditMixin:
    """
    Mixin to add audit functionality for admin actions
    """
    def form_valid(self, form):
        """Set created_by or updated_by fields"""
        if hasattr(form.instance, 'created_by') and not form.instance.pk:
            form.instance.created_by = self.request.user
        
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
            
        return super().form_valid(form)