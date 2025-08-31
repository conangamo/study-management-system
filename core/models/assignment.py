"""
Assignment models
Models cho hệ thống bài tập
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import os
import json

from .study import Course


def default_allowed_file_types():
    """Default allowed file types for assignments"""
    return ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg']

class Assignment(models.Model):
    """Model bài tập"""
    
    STATUS_CHOICES = [
        ('draft', 'Bản nháp'),
        ('active', 'Hoạt động'),
        ('inactive', 'Không hoạt động'),
        ('closed', 'Đã đóng'),
    ]
    
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='assignments',
        verbose_name='Môn học'
    )
    title = models.CharField(
        max_length=200, 
        verbose_name='Tiêu đề bài tập'
    )
    description = models.TextField(
        verbose_name='Mô tả bài tập'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='created_assignments',
        verbose_name='Tạo bởi'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    due_date = models.DateTimeField(
        verbose_name='Hạn nộp'
    )
    max_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Điểm tối đa'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Trạng thái'
    )
    allow_late_submission = models.BooleanField(
        default=False,
        verbose_name='Cho phép nộp muộn'
    )
    max_file_size = models.IntegerField(
        default=10,
        verbose_name='Kích thước file tối đa (MB)'
    )
    allowed_file_types = models.JSONField(
        default=default_allowed_file_types,
        verbose_name='Loại file được phép'
    )
    instructions = models.TextField(
        blank=True,
        verbose_name='Hướng dẫn làm bài'
    )
    is_visible_to_students = models.BooleanField(
        default=False,
        verbose_name='Hiển thị cho sinh viên'
    )
    attachment = models.FileField(
        upload_to='assignments/attachments/',
        blank=True,
        null=True,
        verbose_name='File đính kèm'
    )
    
    class Meta:
        verbose_name = 'Bài tập'
        verbose_name_plural = 'Bài tập'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra due_date phải trong tương lai
        if self.due_date and self.due_date <= timezone.now():
            raise ValidationError('Hạn nộp phải trong tương lai.')
        
        # Kiểm tra max_score
        if self.max_score and self.max_score <= 0:
            raise ValidationError('Điểm tối đa phải lớn hơn 0.')
        
        # Kiểm tra max_file_size
        if self.max_file_size and self.max_file_size <= 0:
            raise ValidationError('Kích thước file tối đa phải lớn hơn 0.')
    
    @property
    def is_overdue(self):
        """Kiểm tra bài tập đã quá hạn chưa"""
        return timezone.now() > self.due_date
    
    @property
    def submission_count(self):
        """Số lượng bài nộp"""
        return self.submissions.count()
    
    @property
    def graded_count(self):
        """Số lượng bài đã chấm điểm"""
        return self.submissions.filter(status='graded').count()
    
    @property
    def late_submission_count(self):
        """Số lượng bài nộp muộn"""
        return self.submissions.filter(status='late').count()
    
    @property
    def pending_grades_count(self):
        """Số lượng bài chưa chấm điểm"""
        return self.submissions.filter(status__in=['submitted', 'late']).count()
    
    def can_be_edited_by(self, user):
        """Kiểm tra user có thể chỉnh sửa bài tập không"""
        if user.is_superuser:
            return True
        return self.created_by == user or self.course.teacher == user
    
    def can_be_viewed_by(self, user):
        """Kiểm tra user có thể xem bài tập không"""
        if user.is_superuser:
            return True
        if self.created_by == user or self.course.teacher == user:
            return True
        # Sinh viên chỉ xem được bài tập active và visible
        if hasattr(user, 'profile') and user.profile.role == 'student':
            return (self.status == 'active' and 
                   self.is_visible_to_students and
                   self.course.students.filter(id=user.id).exists())
        return False


class AssignmentFile(models.Model):
    """Model file đính kèm bài tập"""
    
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Bài tập'
    )
    file = models.FileField(
        upload_to='assignments/files/',
        verbose_name='File'
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name='Tên file'
    )
    file_type = models.CharField(
        max_length=50,
        verbose_name='Loại file'
    )
    file_size = models.BigIntegerField(
        verbose_name='Kích thước file (bytes)'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_assignment_files',
        verbose_name='Upload bởi'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày upload'
    )
    is_submission_file = models.BooleanField(
        default=False,
        verbose_name='Là file bài nộp'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Mô tả file'
    )
    
    class Meta:
        verbose_name = 'File bài tập'
        verbose_name_plural = 'File bài tập'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['assignment', 'is_submission_file']),
            models.Index(fields=['uploaded_by']),
        ]
    
    def __str__(self):
        return f"{self.file_name} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        """Override save để tự động set file info"""
        if self.file and not self.file_name:
            self.file_name = os.path.basename(self.file.name)
        
        if self.file and not self.file_type:
            self.file_type = os.path.splitext(self.file.name)[1].lower()
        
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """Kích thước file tính bằng MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_image(self):
        """Kiểm tra có phải file ảnh không"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        return self.file_type.lower() in image_extensions
    
    @property
    def is_document(self):
        """Kiểm tra có phải file tài liệu không"""
        doc_extensions = ['.pdf', '.doc', '.docx', '.txt']
        return self.file_type.lower() in doc_extensions


class AssignmentSubmission(models.Model):
    """Model bài nộp của sinh viên"""
    
    STATUS_CHOICES = [
        ('submitted', 'Đã nộp'),
        ('late', 'Nộp muộn'),
        ('graded', 'Đã chấm điểm'),
        ('returned', 'Đã trả bài'),
    ]
    
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Bài tập'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
        verbose_name='Sinh viên'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian nộp'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        verbose_name='Trạng thái'
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Điểm số'
    )
    feedback = models.TextField(
        blank=True,
        verbose_name='Nhận xét'
    )
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions',
        verbose_name='Chấm điểm bởi'
    )
    graded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian chấm điểm'
    )
    comments = models.TextField(
        blank=True,
        verbose_name='Ghi chú của sinh viên'
    )
    
    class Meta:
        verbose_name = 'Bài nộp'
        verbose_name_plural = 'Bài nộp'
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student']
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra điểm số không vượt quá điểm tối đa
        if self.grade and self.assignment.max_score:
            if self.grade > self.assignment.max_score:
                raise ValidationError(f'Điểm số không được vượt quá {self.assignment.max_score}.')
    
    def save(self, *args, **kwargs):
        """Override save để tự động set status"""
        # Kiểm tra nộp muộn
        if self.submitted_at and self.assignment.due_date:
            if self.submitted_at > self.assignment.due_date:
                if not self.assignment.allow_late_submission:
                    raise ValidationError('Không được phép nộp muộn.')
                self.status = 'late'
        
        # Cập nhật thời gian chấm điểm
        if self.grade and not self.graded_at:
            self.graded_at = timezone.now()
            self.status = 'graded'
        
        super().save(*args, **kwargs)
    
    @property
    def is_late(self):
        """Kiểm tra có nộp muộn không"""
        return self.submitted_at > self.assignment.due_date
    
    @property
    def is_graded(self):
        """Kiểm tra đã được chấm điểm chưa"""
        return self.status == 'graded' and self.grade is not None
    
    @property
    def grade_percentage(self):
        """Tính phần trăm điểm"""
        if self.grade and self.assignment.max_score:
            return round((self.grade / self.assignment.max_score) * 100, 2)
        return 0
    
    @property
    def files(self):
        """Lấy danh sách file bài nộp"""
        return AssignmentFile.objects.filter(
            assignment=self.assignment,
            uploaded_by=self.student,
            is_submission_file=True
        )
    
    def can_be_viewed_by(self, user):
        """Kiểm tra user có thể xem bài nộp không"""
        if user.is_superuser:
            return True
        if self.student == user:
            return True
        if self.assignment.created_by == user or self.assignment.course.teacher == user:
            return True
        return False


class AssignmentGrade(models.Model):
    """Model điểm số chi tiết"""
    
    submission = models.OneToOneField(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name='detailed_grade',
        verbose_name='Bài nộp'
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Điểm số'
    )
    feedback = models.TextField(
        verbose_name='Nhận xét chi tiết'
    )
    graded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_grades',
        verbose_name='Chấm điểm bởi'
    )
    graded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Thời gian chấm điểm'
    )
    is_final = models.BooleanField(
        default=True,
        verbose_name='Điểm cuối cùng'
    )
    criteria_scores = models.JSONField(
        default=dict,
        verbose_name='Điểm theo tiêu chí'
    )
    rubric_used = models.JSONField(
        default=dict,
        verbose_name='Rubric sử dụng'
    )
    
    class Meta:
        verbose_name = 'Điểm bài tập'
        verbose_name_plural = 'Điểm bài tập'
        ordering = ['-graded_at']
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['graded_by']),
        ]
    
    def __str__(self):
        return f"{self.submission} - {self.score}"
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra điểm số không vượt quá điểm tối đa
        if self.score and self.submission.assignment.max_score:
            if self.score > self.submission.assignment.max_score:
                raise ValidationError(f'Điểm số không được vượt quá {self.submission.assignment.max_score}.')
    
    @property
    def grade_percentage(self):
        """Tính phần trăm điểm"""
        if self.score and self.submission.assignment.max_score:
            return round((self.score / self.submission.assignment.max_score) * 100, 2)
        return 0
    
    @property
    def grade_letter(self):
        """Chuyển đổi điểm số thành chữ cái"""
        percentage = self.grade_percentage
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F' 