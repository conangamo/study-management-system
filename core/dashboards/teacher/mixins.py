"""
Teacher Dashboard Mixins
- Permission checks
- Common functionality
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class TeacherRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure user is logged in and has teacher role
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has teacher profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Tài khoản chưa được thiết lập profile.')
            return redirect('auth:login')
        
        # Check if user is teacher or admin (admin can access teacher dashboard)
        if not (request.user.profile.is_teacher or request.user.profile.is_admin or request.user.is_superuser):
            messages.error(request, 'Bạn không có quyền truy cập vào trang này.')
            raise PermissionDenied("Chỉ giảng viên hoặc admin mới có thể truy cập trang này.")
        
        return super().dispatch(request, *args, **kwargs)


class TeacherOwnContentMixin:
    """
    Mixin to ensure teacher can only access their own content
    """
    def get_queryset(self):
        """Override to filter by teacher"""
        queryset = super().get_queryset()
        return queryset.filter(teacher=self.request.user)
    
    def get_object(self, queryset=None):
        """Override to ensure teacher owns the object"""
        obj = super().get_object(queryset)
        if hasattr(obj, 'teacher') and obj.teacher != self.request.user:
            raise Http404("Bạn không có quyền truy cập nội dung này.")
        return obj


class TeacherCourseAccessMixin:
    """
    Mixin to ensure teacher can only access courses they teach
    """
    def get_queryset(self):
        """Filter queryset to only courses taught by this teacher"""
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'course'):
            return queryset.filter(course__teacher=self.request.user)
        elif hasattr(queryset.model, 'teacher'):
            return queryset.filter(teacher=self.request.user)
        return queryset
    
    def get_object(self, queryset=None):
        """Ensure teacher has access to the object"""
        obj = super().get_object(queryset)
        
        # Check direct teacher relationship
        if hasattr(obj, 'teacher') and obj.teacher != self.request.user:
            raise Http404("Bạn không có quyền truy cập nội dung này.")
        
        # Check course relationship
        if hasattr(obj, 'course') and obj.course.teacher != self.request.user:
            raise Http404("Bạn không có quyền truy cập nội dung này.")
        
        return obj


class TeacherSuccessMessageMixin:
    """
    Mixin to add success messages for teacher actions
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


class TeacherContextMixin:
    """
    Mixin to add common context data for teacher views
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add teacher info
        context['teacher'] = self.request.user
        context['teacher_profile'] = self.request.user.profile
        
        # Add navigation info
        context['dashboard_type'] = 'teacher'
        
        return context 