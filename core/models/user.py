"""
User models - UserProfile, UserRole
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.urls import reverse
from django.core.exceptions import ValidationError
from ..utils.validators import validate_student_id_if_provided


class UserProfile(models.Model):
    """Model mở rộng thông tin người dùng"""
    
    ROLE_CHOICES = [
        ('student', 'Sinh viên'),
        ('teacher', 'Giảng viên'),
        ('admin', 'Quản trị viên'),
    ]
    
    # Legacy department choices for backward compatibility
    DEPARTMENT_CHOICES = [
        ('cntt', 'Công nghệ thông tin'),
        ('kt', 'Kinh tế'),
        ('nn', 'Ngoại ngữ'),
        ('sk', 'Sức khỏe'),
        ('khac', 'Khác'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Số điện thoại không hợp lệ')]
    )
    student_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name='Mã sinh viên',
        validators=[validate_student_id_if_provided]
    )
    
    # Legacy department field (keep for backward compatibility)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    year_of_study = models.IntegerField(blank=True, null=True, verbose_name='Năm học')
    
    # New academic structure links
    academic_department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Khoa'
    )
    major = models.ForeignKey(
        'Major',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Chuyên ngành'
    )
    student_class = models.ForeignKey(
        'StudentClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Lớp học'
    )
    # New class enrollment field for the Class model
    class_enrolled = models.ForeignKey(
        'Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_enrolled_students',
        verbose_name='Lớp đang theo học'
    )
    academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Năm học nhập học'
    )
    
    # Additional academic info
    gpa = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='Điểm trung bình tích lũy'
    )
    credits_earned = models.IntegerField(default=0, verbose_name='Số tín chỉ đã tích lũy')
    
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, verbose_name='Giới thiệu')
    is_verified = models.BooleanField(default=False, verbose_name='Đã xác thực')
    
    # Address info
    address = models.TextField(blank=True, null=True, verbose_name='Địa chỉ')
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Ngày sinh')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_profiles',
        verbose_name='Được tạo bởi'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Thông tin người dùng'
        verbose_name_plural = 'Thông tin người dùng'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"
    
    def get_absolute_url(self):
        return reverse('core:profile', kwargs={'pk': self.pk})
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra student_id cho sinh viên (chỉ khi đã có role)
        if self.role == 'student' and self.student_id is None:
            # Chỉ validate khi đã có role và không có student_id
            # Cho phép tạo user trước, sau đó cập nhật student_id
            pass
        
        # Kiểm tra year_of_study cho sinh viên
        if self.role == 'student' and self.year_of_study:
            if self.year_of_study < 2000 or self.year_of_study > 2030:
                raise ValidationError('Năm học phải từ 2000 đến 2030.')
        
        # Kiểm tra department cho sinh viên
        if self.role == 'student' and not self.department:
            # Chỉ validate khi đã có role
            pass
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Trả về họ tên đầy đủ"""
        return self.user.get_full_name() or self.user.username
    
    @property
    def is_student(self):
        """Kiểm tra có phải sinh viên không"""
        return self.role == 'student'
    
    @property
    def is_teacher(self):
        """Kiểm tra có phải giảng viên không"""
        return self.role == 'teacher'
    
    @property
    def is_admin(self):
        """Kiểm tra có phải admin không"""
        return self.role == 'admin'
    
    @property
    def can_create_student_accounts(self):
        """Kiểm tra quyền tạo tài khoản sinh viên"""
        return self.role in ['teacher', 'admin']
    
    @property
    def can_manage_users(self):
        """Kiểm tra quyền quản lý người dùng"""
        return self.role == 'admin'
    
    @property
    def can_change_password(self):
        """Kiểm tra quyền đổi mật khẩu"""
        return True  # Tất cả user đều có thể đổi mật khẩu


class UserRole(models.Model):
    """Model quản lý vai trò người dùng"""
    
    ROLE_CHOICES = [
        ('student', 'Sinh viên'),
        ('teacher', 'Giảng viên'),
        ('admin', 'Quản trị viên'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vai trò người dùng'
        verbose_name_plural = 'Vai trò người dùng'
        unique_together = ['user', 'role']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra không có duplicate roles cho cùng một user
        if UserRole.objects.filter(user=self.user, role=self.role).exclude(pk=self.pk).exists():
            raise ValidationError('Người dùng này đã có vai trò này.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs) 