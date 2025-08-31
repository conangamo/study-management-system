"""
Request models - StudentAccountRequest
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from .user import UserProfile
from ..utils.validators import validate_student_id_if_provided


class StudentAccountRequest(models.Model):
    """Model quản lý yêu cầu tạo tài khoản sinh viên"""
    
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
        ('completed', 'Đã tạo tài khoản'),
    ]
    
    student_id = models.CharField(
        max_length=50, 
        verbose_name='Mã sinh viên',
        validators=[validate_student_id_if_provided]
    )
    email = models.EmailField(verbose_name='Email')
    first_name = models.CharField(max_length=30, verbose_name='Họ')
    last_name = models.CharField(max_length=30, verbose_name='Tên')
    department = models.CharField(max_length=100, choices=UserProfile.DEPARTMENT_CHOICES, verbose_name='Khoa/Ngành')
    year_of_study = models.IntegerField(verbose_name='Năm học')
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='Số điện thoại',
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Số điện thoại không hợp lệ')]
    )
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_requests', 
        verbose_name='Yêu cầu bởi'
    )
    created_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_student_accounts', 
        verbose_name='Tài khoản được tạo'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')
    notes = models.TextField(blank=True, null=True, verbose_name='Ghi chú')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Yêu cầu tạo tài khoản sinh viên'
        verbose_name_plural = 'Yêu cầu tạo tài khoản sinh viên'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name} - {self.get_status_display()}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def approve(self, approved_by):
        """Duyệt yêu cầu"""
        self.status = 'approved'
        self.save()
    
    def reject(self, rejected_by, reason=''):
        """Từ chối yêu cầu"""
        self.status = 'rejected'
        self.notes = reason
        self.save()
    
    def complete(self, created_user):
        """Hoàn thành tạo tài khoản"""
        self.status = 'completed'
        self.created_user = created_user
        self.save()
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra year_of_study
        if self.year_of_study < 2000 or self.year_of_study > 2030:
            raise ValidationError('Năm học phải từ 2000 đến 2030.')
        
        # Kiểm tra email không được trống
        if not self.email:
            raise ValidationError('Email không được để trống.')
        
        # Kiểm tra first_name và last_name
        if not self.first_name or not self.last_name:
            raise ValidationError('Họ và tên không được để trống.')
        
        # Kiểm tra department
        if not self.department:
            raise ValidationError('Khoa/Ngành không được để trống.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs) 