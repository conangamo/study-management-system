from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count

from ..models import LoginHistory, PasswordReset, AccountLockout


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin cho LoginHistory"""
    list_display = ('user', 'login_time', 'logout_time', 'ip_address', 'success', 'session_duration')
    list_filter = ('success', 'login_time', 'ip_address')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'ip_address')
    ordering = ('-login_time',)
    readonly_fields = ('user', 'login_time', 'logout_time', 'ip_address', 'user_agent', 'success', 'failure_reason')
    
    fieldsets = (
        ('Thông tin đăng nhập', {
            'fields': ('user', 'login_time', 'logout_time', 'ip_address', 'user_agent')
        }),
        ('Kết quả', {
            'fields': ('success', 'failure_reason')
        }),
    )
    
    def session_duration(self, obj):
        """Hiển thị thời gian session"""
        duration = obj.session_duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return '-'
    session_duration.short_description = 'Thời gian session'
    
    def get_queryset(self, request):
        """Optimize queryset với select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Admin cho PasswordReset"""
    list_display = ('user', 'created_at', 'expires_at', 'used', 'is_valid')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'token', 'created_at', 'expires_at', 'used')
    
    fieldsets = (
        ('Thông tin reset', {
            'fields': ('user', 'token', 'created_at', 'expires_at', 'used')
        }),
    )
    
    def is_valid(self, obj):
        """Kiểm tra token có hợp lệ không"""
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Còn hiệu lực'
    
    def get_queryset(self, request):
        """Optimize queryset với select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(AccountLockout)
class AccountLockoutAdmin(admin.ModelAdmin):
    """Admin cho AccountLockout"""
    list_display = ('user', 'ip_address', 'failed_attempts', 'locked_until', 'is_locked')
    list_filter = ('failed_attempts', 'created_at', 'updated_at')
    search_fields = ('user__username', 'ip_address')
    ordering = ('-updated_at',)
    readonly_fields = ('user', 'ip_address', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin khóa tài khoản', {
            'fields': ('user', 'ip_address', 'failed_attempts', 'locked_until')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_locked(self, obj):
        """Kiểm tra tài khoản có bị khóa không"""
        return obj.is_locked()
    is_locked.boolean = True
    is_locked.short_description = 'Đang bị khóa'
    
    actions = ['reset_lockout']
    
    def reset_lockout(self, request, queryset):
        """Reset khóa tài khoản"""
        for lockout in queryset:
            lockout.reset_failed_attempts()
        self.message_user(request, f'Đã reset {queryset.count()} khóa tài khoản.')
    reset_lockout.short_description = 'Reset khóa tài khoản đã chọn'
    
    def get_queryset(self, request):
        """Optimize queryset với select_related"""
        return super().get_queryset(request).select_related('user') 