"""
Common Dashboard Views
- Dashboard redirect based on user role
- Profile management
- Common utilities
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View, UpdateView, ListView
from django.contrib import messages
from django.urls import reverse_lazy


class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Redirect user to appropriate dashboard based on their role
    """
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Tài khoản chưa được thiết lập profile.')
            return redirect('core:profile')
        
        user_role = request.user.profile.role
        
        if user_role == 'student':
            return redirect('core:dashboards:student:dashboard')
        elif user_role == 'teacher':
            return redirect('core:dashboards:teacher:dashboard')
        elif user_role == 'admin':
            return redirect('core:dashboards:admin:dashboard')
        else:
            messages.error(request, 'Vai trò người dùng không hợp lệ.')
            return redirect('core:home')


class ProfileView(LoginRequiredMixin, TemplateView):
    """View user profile"""
    template_name = 'dashboards/common/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = getattr(self.request.user, 'profile', None)
        return context


class ProfileEditView(LoginRequiredMixin, TemplateView):
    """Edit user profile"""
    template_name = 'dashboards/common/profile_edit.html'
    
    # This would need a proper form and implementation
    pass


class NotificationListView(LoginRequiredMixin, ListView):
    """List user notifications"""
    template_name = 'dashboards/common/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        # This would need a Notification model
        return []


class MarkNotificationsReadView(LoginRequiredMixin, View):
    """Mark notifications as read"""
    def post(self, request, *args, **kwargs):
        # Implementation would mark notifications as read
        messages.success(request, 'Đã đánh dấu tất cả thông báo là đã đọc.')
        return redirect('dashboards:common:notifications') 