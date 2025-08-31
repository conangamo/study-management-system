"""
Academic Structure Models
- Academic Years, Semesters, Departments, Majors
- Real university academic structure
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

class AcademicYear(models.Model):
    """Model quản lý năm học"""
    
    name = models.CharField(max_length=9, unique=True, verbose_name='Năm học')  # 2024-2025
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    is_current = models.BooleanField(default=False, verbose_name='Năm học hiện tại')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Năm học'
        verbose_name_plural = 'Năm học'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        # Validate year format (YYYY-YYYY)
        if not re.match(r'^\d{4}-\d{4}$', self.name):
            raise ValidationError('Năm học phải có định dạng YYYY-YYYY')
        
        # Validate start_date < end_date
        if self.start_date >= self.end_date:
            raise ValidationError('Ngày bắt đầu phải nhỏ hơn ngày kết thúc')
        
        # Only one current academic year
        if self.is_current:
            existing = AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError('Chỉ có thể có một năm học hiện tại')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_current(cls):
        """Get current academic year"""
        return cls.objects.filter(is_current=True).first()


class Department(models.Model):
    """Model quản lý khoa/bộ môn"""
    
    name = models.CharField(max_length=200, verbose_name='Tên khoa')
    code = models.CharField(max_length=10, unique=True, verbose_name='Mã khoa')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Số điện thoại')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    address = models.TextField(blank=True, null=True, verbose_name='Địa chỉ')
    
    # Academic structure
    dean = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_departments',
        verbose_name='Trưởng khoa'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Khoa'
        verbose_name_plural = 'Khoa'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Major(models.Model):
    """Model quản lý chuyên ngành"""
    
    DEGREE_CHOICES = [
        ('bachelor', 'Cử nhân'),
        ('master', 'Thạc sĩ'),
        ('doctor', 'Tiến sĩ'),
        ('associate', 'Cao đẳng'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Tên chuyên ngành')
    code = models.CharField(max_length=15, unique=True, verbose_name='Mã ngành')
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='majors',
        verbose_name='Khoa'
    )
    
    # Academic details
    degree_type = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='bachelor', verbose_name='Loại bằng')
    duration_years = models.IntegerField(default=4, verbose_name='Thời gian đào tạo (năm)')
    total_credits = models.IntegerField(default=140, verbose_name='Tổng số tín chỉ')
    
    # Curriculum
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả chuyên ngành')
    career_prospects = models.TextField(blank=True, null=True, verbose_name='Triển vọng nghề nghiệp')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Chuyên ngành'
        verbose_name_plural = 'Chuyên ngành'
        ordering = ['department', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class StudentClass(models.Model):
    """Model quản lý lớp học"""
    
    name = models.CharField(max_length=20, unique=True, verbose_name='Tên lớp')  # ITE2023A
    major = models.ForeignKey(
        Major, 
        on_delete=models.CASCADE, 
        related_name='classes',
        verbose_name='Chuyên ngành'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name='Năm học'
    )
    
    # Class details
    year_of_study = models.IntegerField(verbose_name='Năm học')  # 1, 2, 3, 4
    max_students = models.IntegerField(default=40, verbose_name='Sĩ số tối đa')
    
    # Class advisor
    advisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advised_classes',
        verbose_name='Cố vấn học tập'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Lớp học'
        verbose_name_plural = 'Lớp học'
        ordering = ['academic_year', 'major', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def student_count(self):
        """Số lượng sinh viên trong lớp"""
        return self.students.count()
    
    @property
    def is_full(self):
        """Kiểm tra lớp đã đầy chưa"""
        return self.student_count >= self.max_students


class CourseCategory(models.Model):
    """Model phân loại môn học"""
    
    CATEGORY_CHOICES = [
        ('general', 'Đại cương'),
        ('foundation', 'Cơ sở'),
        ('major', 'Chuyên ngành'),
        ('elective', 'Tự chọn'),
        ('thesis', 'Luận văn/Đồ án'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    code = models.CharField(max_length=10, unique=True, verbose_name='Mã danh mục')
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Loại danh mục')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    
    # Credit requirements
    min_credits = models.IntegerField(default=0, verbose_name='Tín chỉ tối thiểu')
    max_credits = models.IntegerField(null=True, blank=True, verbose_name='Tín chỉ tối đa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Danh mục môn học'
        verbose_name_plural = 'Danh mục môn học'
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Curriculum(models.Model):
    """Model chương trình đào tạo"""
    
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name='curriculums',
        verbose_name='Chuyên ngành'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='curriculums',
        verbose_name='Năm học áp dụng'
    )
    
    name = models.CharField(max_length=200, verbose_name='Tên chương trình')
    version = models.CharField(max_length=10, verbose_name='Phiên bản')  # v1.0, v2.1
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Đang áp dụng')
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_curriculums',
        verbose_name='Được phê duyệt bởi'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Ngày phê duyệt')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Chương trình đào tạo'
        verbose_name_plural = 'Chương trình đào tạo'
        unique_together = ['major', 'academic_year', 'version']
        ordering = ['-academic_year', 'major', 'version']
    
    def __str__(self):
        return f"{self.major.code} - {self.name} ({self.version})" 