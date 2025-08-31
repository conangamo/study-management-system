"""
Authentication models - LoginHistory, PasswordReset, AccountLockout
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class LoginHistory(models.Model):
    """Model lưu lịch sử đăng nhập"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Lịch sử đăng nhập'
        verbose_name_plural = 'Lịch sử đăng nhập'
        ordering = ['-login_time']
    
    def __str__(self):
        status = "Thành công" if self.success else "Thất bại"
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')} - {status}"
    
    @property
    def session_duration(self):
        """Tính thời gian session"""
        if self.logout_time:
            return self.logout_time - self.login_time
        return None
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra logout_time phải sau login_time
        if self.logout_time and self.logout_time < self.login_time:
            raise ValidationError('Thời gian đăng xuất phải sau thời gian đăng nhập.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class PasswordReset(models.Model):
    """Model quản lý đặt lại mật khẩu"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Đặt lại mật khẩu'
        verbose_name_plural = 'Đặt lại mật khẩu'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_expired(self):
        """Kiểm tra token có hết hạn không"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Kiểm tra token có hợp lệ không"""
        return not self.used and not self.is_expired()
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra expires_at phải sau created_at
        if self.expires_at <= self.created_at:
            raise ValidationError('Thời gian hết hạn phải sau thời gian tạo.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class AccountLockout(models.Model):
    """Model quản lý khóa tài khoản"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lockouts')
    ip_address = models.GenericIPAddressField()
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Khóa tài khoản'
        verbose_name_plural = 'Khóa tài khoản'
        unique_together = ['user', 'ip_address']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.failed_attempts} lần thất bại"
    
    def is_locked(self):
        """Kiểm tra tài khoản có bị khóa không"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    def increment_failed_attempts(self):
        """Tăng số lần thất bại"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:  # Khóa sau 5 lần thất bại
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save()
    
    def reset_failed_attempts(self):
        """Reset số lần thất bại"""
        self.failed_attempts = 0
        self.locked_until = None
        self.save()
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra failed_attempts không âm
        if self.failed_attempts < 0:
            raise ValidationError('Số lần thất bại không thể âm.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs) 