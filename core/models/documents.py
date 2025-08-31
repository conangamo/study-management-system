"""
Documents models
Models cho quản lý tài liệu học tập
"""
import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse


def document_upload_path(instance, filename):
    """Tạo đường dẫn upload cho tài liệu"""
    now = timezone.now()
    return f'documents/{instance.course.id}/{now.year}/{now.month:02d}/{filename}'


class DocumentCategory(models.Model):
    """Danh mục tài liệu"""
    
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Màu sắc')
    icon = models.CharField(max_length=50, default='fas fa-file', verbose_name='Icon')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_document_categories',
        verbose_name='Tạo bởi'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Danh mục tài liệu'
        verbose_name_plural = 'Danh mục tài liệu'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Document(models.Model):
    """Model quản lý tài liệu học tập"""
    
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('doc', 'DOC'),
        ('ppt', 'PPT'),
        ('pptx', 'PPTX'),
        ('xls', 'XLS'),
        ('xlsx', 'XLSX'),
        ('txt', 'TXT'),
        ('png', 'PNG'),
        ('jpg', 'JPG'),
        ('jpeg', 'JPEG'),
        ('gif', 'GIF'),
        ('mp4', 'MP4'),
        ('mp3', 'MP3'),
        ('zip', 'ZIP'),
        ('rar', 'RAR'),
        ('other', 'Khác'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Hoạt động'),
        ('archived', 'Đã lưu trữ'),
        ('deleted', 'Đã xóa'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Công khai'),
        ('private', 'Riêng tư'),
        ('course_only', 'Chỉ môn học'),
    ]
    
    # Thông tin cơ bản
    title = models.CharField(max_length=200, verbose_name='Tiêu đề')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    course = models.ForeignKey(
        'core.Course', 
        on_delete=models.CASCADE, 
        related_name='documents',
        verbose_name='Môn học'
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name='Danh mục'
    )
    
    # File information
    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name='File tài liệu'
    )
    file_name = models.CharField(max_length=255, verbose_name='Tên file gốc')
    file_size = models.BigIntegerField(verbose_name='Kích thước file (bytes)')
    file_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES, verbose_name='Loại file')
    
    # Upload information
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='uploaded_documents',
        verbose_name='Người tải lên'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian tải lên')
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Trạng thái')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public', verbose_name='Quyền xem')
    
    # Download tracking
    download_count = models.IntegerField(default=0, verbose_name='Số lần tải về')
    last_downloaded_at = models.DateTimeField(null=True, blank=True, verbose_name='Lần tải về cuối')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tài liệu'
        verbose_name_plural = 'Tài liệu'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"
    
    def get_absolute_url(self):
        return reverse('core:document_detail', kwargs={'pk': self.pk})
    
    @property
    def file_size_mb(self):
        """Trả về kích thước file theo MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def file_extension(self):
        """Trả về phần mở rộng của file"""
        return os.path.splitext(self.file_name)[1].lower()
    
    def increment_download_count(self):
        """Tăng số lượt tải về"""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded_at'])
    
    def can_be_edited_by(self, user):
        """Kiểm tra xem user có thể chỉnh sửa tài liệu không"""
        if user.is_superuser:
            return True
        
        # Giáo viên phụ trách môn học
        if hasattr(user, 'userprofile') and user.userprofile.role == 'teacher':
            return self.course.teacher == user or user in self.course.assistant_teachers.all()
        
        return False
    
    def can_be_deleted_by(self, user):
        """Kiểm tra xem user có thể xóa tài liệu không"""
        return self.can_be_edited_by(user)
    
    def can_be_viewed_by(self, user):
        """Kiểm tra xem user có thể xem tài liệu không"""
        if self.status != 'active':
            return False
        
        if self.visibility == 'public':
            return True
        
        if self.visibility == 'course_only':
            # Sinh viên đăng ký môn học hoặc giáo viên phụ trách
            if hasattr(user, 'userprofile'):
                if user.userprofile.role == 'student':
                    return self.course.students.filter(id=user.id).exists()
                elif user.userprofile.role == 'teacher':
                    return self.course.teacher == user or user in self.course.assistant_teachers.all()
        
        if self.visibility == 'private':
            return self.uploaded_by == user
        
        return False
    
    def clean(self):
        """Validation cho model"""
        # Kiểm tra file size nếu có
        if self.file_size is not None and self.file_size > 100 * 1024 * 1024:  # 100MB
            raise ValidationError('Kích thước file không được vượt quá 100MB')
        
        # Kiểm tra file type
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            allowed_extensions = ['.pdf', '.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx', 
                                '.txt', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3', '.zip', '.rar']
            if ext not in allowed_extensions:
                raise ValidationError(f'Loại file {ext} không được hỗ trợ')
    
    def save(self, *args, **kwargs):
        """Override save method để tự động set file information"""
        if self.file and not self.file_name:
            self.file_name = os.path.basename(self.file.name)
            self.file_size = self.file.size
            
            # Xác định file type
            ext = os.path.splitext(self.file.name)[1].lower()
            ext_to_type = {
                '.pdf': 'pdf', '.docx': 'docx', '.doc': 'doc', '.ppt': 'ppt', '.pptx': 'pptx',
                '.xls': 'xls', '.xlsx': 'xlsx', '.txt': 'txt', '.png': 'png', '.jpg': 'jpg',
                '.jpeg': 'jpeg', '.gif': 'gif', '.mp4': 'mp4', '.mp3': 'mp3', '.zip': 'zip', '.rar': 'rar'
            }
            self.file_type = ext_to_type.get(ext, 'other')
        
        # Đảm bảo file_size không bao giờ là None
        if self.file_size is None and self.file:
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)


class DocumentDownloadLog(models.Model):
    """Model ghi log việc tải tài liệu"""
    
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE, 
        related_name='download_logs',
        verbose_name='Tài liệu'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='document_downloads',
        verbose_name='Người tải'
    )
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian tải')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='Địa chỉ IP')
    user_agent = models.TextField(blank=True, null=True, verbose_name='User Agent')
    
    class Meta:
        verbose_name = 'Log tải tài liệu'
        verbose_name_plural = 'Log tải tài liệu'
        ordering = ['-downloaded_at']
    
    def __str__(self):
        return f"{self.user.username} tải {self.document.title} lúc {self.downloaded_at}"


class DocumentComment(models.Model):
    """Model cho bình luận tài liệu"""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Tài liệu'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='document_comments',
        verbose_name='Người bình luận'
    )
    content = models.TextField(verbose_name='Nội dung bình luận')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian bình luận')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Thời gian cập nhật')
    
    class Meta:
        verbose_name = 'Bình luận tài liệu'
        verbose_name_plural = 'Bình luận tài liệu'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bình luận của {self.user.username} về {self.document.title}" 