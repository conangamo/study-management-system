"""
Study management models - Course, Assignment, Grade, Note, Tag
"""
import re
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import logging

logger = logging.getLogger(__name__)


class Course(models.Model):
    """Model quản lý môn học/khóa học"""
    
    SEMESTER_CHOICES = [
        ('1', 'Học kỳ 1'),
        ('2', 'Học kỳ 2'),
        ('3', 'Học kỳ 3'),
        ('summer', 'Học kỳ hè'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Đang diễn ra'),
        ('completed', 'Đã hoàn thành'),
        ('upcoming', 'Sắp diễn ra'),
        ('cancelled', 'Đã hủy'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Cơ bản'),
        ('intermediate', 'Trung bình'),
        ('advanced', 'Nâng cao'),
        ('expert', 'Chuyên sâu'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Tên môn học')
    code = models.CharField(max_length=20, unique=True, verbose_name='Mã môn học')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    credits = models.IntegerField(default=3, verbose_name='Số tín chỉ')
    
    # Academic structure links
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Khoa'
    )
    category = models.ForeignKey(
        'CourseCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Danh mục môn học'
    )
    academic_year = models.ForeignKey(
        'AcademicYear',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Năm học'
    )
    
    # Course timing
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, verbose_name='Học kỳ')
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    
    # Course details
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate', verbose_name='Độ khó')
    language = models.CharField(max_length=50, default='Tiếng Việt', verbose_name='Ngôn ngữ giảng dạy')
    
    # Prerequisites
    prerequisites = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='dependent_courses',
        verbose_name='Môn học tiên quyết'
    )
    
    # Teaching info
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='teaching_courses',
        verbose_name='Giảng viên phụ trách'
    )
    assistant_teachers = models.ManyToManyField(
        User,
        blank=True,
        related_name='assisting_courses',
        verbose_name='Giảng viên hỗ trợ'
    )
    
    # Enrollment
    students = models.ManyToManyField(
        User,
        through='CourseEnrollment',
        related_name='enrolled_courses',
        verbose_name='Sinh viên đăng ký'
    )
    max_students = models.IntegerField(default=50, verbose_name='Số sinh viên tối đa')
    
    # Content
    syllabus = models.TextField(blank=True, null=True, verbose_name='Nội dung môn học')
    learning_outcomes = models.TextField(blank=True, null=True, verbose_name='Mục tiêu học tập')
    assessment_method = models.TextField(blank=True, null=True, verbose_name='Phương pháp đánh giá')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', verbose_name='Trạng thái')
    is_online = models.BooleanField(default=False, verbose_name='Học trực tuyến')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Môn học'
        verbose_name_plural = 'Môn học'
        ordering = ['-academic_year', 'semester', 'name']
        indexes = [
            models.Index(fields=['teacher']),
            models.Index(fields=['status']),
            models.Index(fields=['academic_year', 'semester']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.academic_year})"
    
    def get_absolute_url(self):
        return reverse('core:course_detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        """Kiểm tra môn học có đang diễn ra không"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status == 'active'
    
    @property
    def student_count(self):
        """Số lượng sinh viên đăng ký"""
        return self.students.count()
    
    @property
    def enrolled_student_count(self):
        """Số lượng sinh viên đã đăng ký (chỉ status enrolled)"""
        return self.enrollments.filter(status='enrolled').count()
    
    @property
    def is_full(self):
        """Kiểm tra môn học đã đầy chưa"""
        return self.enrolled_student_count >= self.max_students
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra end_date không được sớm hơn start_date
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('Ngày kết thúc không được sớm hơn ngày bắt đầu.')
        
        # Kiểm tra credits
        if self.credits <= 0:
            raise ValidationError('Số tín chỉ phải lớn hơn 0.')
        
        # Kiểm tra max_students
        if self.max_students <= 0:
            raise ValidationError('Số sinh viên tối đa phải lớn hơn 0.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class CourseEnrollment(models.Model):
    """Model quản lý việc đăng ký môn học"""
    
    STATUS_CHOICES = [
        ('enrolled', 'Đã đăng ký'),
        ('dropped', 'Đã rút'),
        ('completed', 'Đã hoàn thành'),
        ('failed', 'Trượt'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled', verbose_name='Trạng thái')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian đăng ký')
    dropped_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời gian rút')
    final_grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='Điểm cuối kỳ'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Ghi chú')
    
    class Meta:
        verbose_name = 'Đăng ký môn học'
        verbose_name_plural = 'Đăng ký môn học'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['course']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.name}"
    
    def drop_course(self):
        """Rút môn học"""
        self.status = 'dropped'
        self.dropped_at = timezone.now()
        self.save()
    
    def complete_course(self, final_grade=None):
        """Hoàn thành môn học"""
        self.status = 'completed'
        if final_grade is not None:
            self.final_grade = final_grade
        self.save()
    
    def fail_course(self):
        """Trượt môn học"""
        self.status = 'failed'
        self.save()
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra final_grade
        if self.final_grade is not None:
            if self.final_grade < 0 or self.final_grade > 10:
                raise ValidationError('Điểm phải từ 0 đến 10.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class Grade(models.Model):
    """Model quản lý điểm số"""
    
    GRADE_TYPES = [
        ('assignment', 'Bài tập'),
        ('midterm', 'Giữa kỳ'),
        ('final', 'Cuối kỳ'),
        ('participation', 'Tham gia'),
        ('other', 'Khác'),
    ]
    
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='grades',
        verbose_name='Sinh viên'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='grades',
        verbose_name='Môn học'
    )
    assignment = models.ForeignKey(
        'Assignment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='grades',
        verbose_name='Bài tập'
    )
    submission = models.ForeignKey(
        'AssignmentSubmission', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='grades',
        verbose_name='Bài nộp'
    )
    
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPES, default='assignment', verbose_name='Loại điểm')
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Điểm số')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, verbose_name='Điểm tối đa')
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.00, verbose_name='Trọng số')
    
    # Thông tin bổ sung
    date = models.DateField(verbose_name='Ngày chấm điểm')
    comment = models.TextField(blank=True, null=True, verbose_name='Nhận xét')
    is_final = models.BooleanField(default=False, verbose_name='Điểm cuối cùng')
    
    # Metadata
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_grades',
        verbose_name='Chấm điểm bởi'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Điểm số'
        verbose_name_plural = 'Điểm số'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['course']),
            models.Index(fields=['assignment']),
            models.Index(fields=['grade_type']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.name} - {self.score}/{self.max_score}"
    
    @property
    def percentage(self):
        """Tính phần trăm điểm"""
        if self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0
    
    @property
    def letter_grade(self):
        """Chuyển đổi sang điểm chữ"""
        percentage = self.percentage
        
        if percentage >= 90:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 80:
            return 'B+'
        elif percentage >= 75:
            return 'B'
        elif percentage >= 70:
            return 'C+'
        elif percentage >= 65:
            return 'C'
        elif percentage >= 60:
            return 'D+'
        elif percentage >= 55:
            return 'D'
        else:
            return 'F'
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra score
        if self.score < 0 or self.score > self.max_score:
            raise ValidationError(f'Điểm phải từ 0 đến {self.max_score}.')
        
        # Kiểm tra max_score
        if self.max_score <= 0:
            raise ValidationError('Điểm tối đa phải lớn hơn 0.')
        
        # Kiểm tra weight
        if self.weight <= 0:
            raise ValidationError('Trọng số phải lớn hơn 0.')
        
        # Kiểm tra assignment và submission phải cùng course
        if self.assignment and self.assignment.course != self.course:
            raise ValidationError('Bài tập phải thuộc về môn học này.')
        
        if self.submission and self.submission.assignment != self.assignment:
            raise ValidationError('Bài nộp phải thuộc về bài tập này.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Model quản lý tags cho ghi chú"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Tên tag')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Màu sắc')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tags',
        verbose_name='Tạo bởi'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra color format
        if self.color and not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
            raise ValidationError('Màu sắc phải có định dạng hex (#RRGGBB).')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class Note(models.Model):
    """Model quản lý ghi chú cá nhân"""
    
    PRIORITY_CHOICES = [
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notes',
        verbose_name='Người dùng'
    )
    title = models.CharField(max_length=200, verbose_name='Tiêu đề')
    content = models.TextField(verbose_name='Nội dung')
    tags = models.ManyToManyField(
        Tag, 
        blank=True, 
        related_name='notes',
        verbose_name='Tags'
    )
    
    # Thuộc tính
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Độ ưu tiên')
    is_important = models.BooleanField(default=False, verbose_name='Quan trọng')
    is_pinned = models.BooleanField(default=False, verbose_name='Ghim')
    is_public = models.BooleanField(default=False, verbose_name='Công khai')
    
    # Liên kết với khóa học/bài tập (tùy chọn)
    course = models.ForeignKey(
        Course, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='notes',
        verbose_name='Liên quan đến môn học'
    )
    assignment = models.ForeignKey(
        'Assignment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='notes',
        verbose_name='Liên quan đến bài tập'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ghi chú'
        verbose_name_plural = 'Ghi chú'
        ordering = ['-is_pinned', '-is_important', '-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_important']),
            models.Index(fields=['is_pinned']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('core:note_detail', kwargs={'pk': self.pk})
    
    @property
    def preview(self):
        """Preview nội dung ghi chú"""
        return self.content[:100] + '...' if len(self.content) > 100 else self.content
    
    @property
    def tag_names(self):
        """Trả về danh sách tên tags"""
        return [tag.name for tag in self.tags.all()]
    
    def clean(self):
        """Validation tùy chỉnh"""
        super().clean()
        
        # Kiểm tra assignment phải thuộc về course nếu có
        if self.assignment and self.course and self.assignment.course != self.course:
            raise ValidationError('Bài tập phải thuộc về môn học đã chọn.')
    
    def save(self, *args, **kwargs):
        """Override save để validation"""
        self.full_clean()
        super().save(*args, **kwargs) 


class Class(models.Model):
    """
    Model quản lý lớp học
    """
    YEAR_CHOICES = [
        (2020, '2020'),
        (2021, '2021'),
        (2022, '2022'),
        (2023, '2023'),
        (2024, '2024'),
        (2025, '2025'),
        (2026, '2026'),
        (2027, '2027'),
        (2028, '2028'),
        (2029, '2029'),
        (2030, '2030'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('IT', 'Công nghệ thông tin'),
        ('KT', 'Kế toán'),
        ('QT', 'Quản trị kinh doanh'),
        ('NN', 'Ngoại ngữ'),
        ('KT', 'Kinh tế'),
        ('KH', 'Khoa học'),
        ('GD', 'Giáo dục'),
        ('YT', 'Y tế'),
        ('XH', 'Xã hội học'),
        ('KHAC', 'Khác'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Đang hoạt động'),
        ('inactive', 'Tạm ngưng'),
        ('graduated', 'Đã tốt nghiệp'),
        ('suspended', 'Tạm đình chỉ'),
    ]
    
    # Thông tin cơ bản
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Tên lớp',
        help_text='Ví dụ: 20IT1, 21KT2, 22QT3...'
    )
    
    display_name = models.CharField(
        max_length=100,
        verbose_name='Tên hiển thị',
        help_text='Tên đầy đủ của lớp, ví dụ: Lớp Công nghệ thông tin K20'
    )
    
    # Thông tin năm học và khoa
    academic_year = models.IntegerField(
        choices=YEAR_CHOICES,
        verbose_name='Năm học',
        help_text='Năm sinh viên nhập học'
    )
    
    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES,
        verbose_name='Khoa/Ngành'
    )
    
    class_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name='Số lớp',
        help_text='Số thứ tự của lớp trong khoa (1-20)'
    )
    
    # Thông tin quản lý
    advisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_advised_classes',
        verbose_name='Cố vấn học tập',
        help_text='Giảng viên cố vấn cho lớp'
    )
    
    head_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='new_headed_classes',
        verbose_name='Giáo viên chủ nhiệm'
    )
    
    # Thông tin sinh viên
    max_students = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Sĩ số tối đa'
    )
    
    current_students = models.IntegerField(
        default=0,
        verbose_name='Sĩ số hiện tại'
    )
    
    # Trạng thái và thông tin khác
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Trạng thái'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Mô tả',
        help_text='Thông tin bổ sung về lớp học'
    )
    
    # Thông tin tạo và cập nhật
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='new_created_classes',
        verbose_name='Người tạo'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        verbose_name = 'Lớp học'
        verbose_name_plural = 'Lớp học'
        ordering = ['-academic_year', 'department', 'class_number']
        unique_together = ['academic_year', 'department', 'class_number']
        indexes = [
            models.Index(fields=['academic_year', 'department']),
            models.Index(fields=['status']),
            models.Index(fields=['advisor']),
            models.Index(fields=['head_teacher']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_department_display()}"
    
    def save(self, *args, **kwargs):
        """Override save để tự động tạo tên lớp và cập nhật sĩ số"""
        # Tạo tên lớp tự động chỉ khi chưa có và đang tạo mới
        if not self.name and not self.pk:
            self.name = self.generate_class_name()
        
        # Tạo tên hiển thị tự động chỉ khi chưa có và đang tạo mới
        if not self.display_name and not self.pk:
            self.display_name = self.generate_display_name()
        
        # Lưu trước để có pk
        super().save(*args, **kwargs)
        
        # Cập nhật sĩ số hiện tại sau khi đã lưu
        self.update_student_count()
        
        # Lưu lại nếu sĩ số thay đổi
        if self.pk:  # Chỉ lưu lại nếu đã có pk
            super().save(update_fields=['current_students'])
        
        # Log thay đổi
        logger.info(f"Class {self.name} saved by {self.created_by}")
    
    def generate_class_name(self):
        """Tạo tên lớp tự động theo format: 20IT1, 21KT2..."""
        year_suffix = str(self.academic_year)[-2:]  # Lấy 2 số cuối của năm
        return f"{year_suffix}{self.department}{self.class_number}"
    
    def generate_display_name(self):
        """Tạo tên hiển thị đầy đủ"""
        return f"Lớp {self.get_department_display()} K{self.academic_year} - Lớp {self.class_number}"
    
    def update_student_count(self):
        """Cập nhật số lượng sinh viên hiện tại"""
        from .user import UserProfile
        count = UserProfile.objects.filter(
            role='student',
            class_enrolled=self
        ).count()
        self.current_students = count
    
    def get_students(self):
        """Lấy danh sách sinh viên trong lớp"""
        from .user import UserProfile
        return UserProfile.objects.filter(
            role='student',
            class_enrolled=self
        ).select_related('user')
    
    def add_student(self, student_profile):
        """Thêm sinh viên vào lớp"""
        if self.current_students >= self.max_students:
            raise ValueError(f"Lớp {self.name} đã đầy ({self.max_students} sinh viên)")
        
        if student_profile.role != 'student':
            raise ValueError("Chỉ có thể thêm sinh viên vào lớp")
        
        student_profile.class_enrolled = self
        student_profile.save()
        self.update_student_count()
        self.save()
        
        logger.info(f"Student {student_profile.user.username} added to class {self.name}")
    
    def remove_student(self, student_profile):
        """Xóa sinh viên khỏi lớp"""
        if student_profile.class_enrolled == self:
            student_profile.class_enrolled = None
            student_profile.save()
            self.update_student_count()
            self.save()
            
            logger.info(f"Student {student_profile.user.username} removed from class {self.name}")
    
    def is_full(self):
        """Kiểm tra lớp đã đầy chưa"""
        return self.current_students >= self.max_students
    
    def get_available_slots(self):
        """Lấy số chỗ trống còn lại"""
        return max(0, self.max_students - self.current_students)
    
    def get_academic_progress(self):
        """Lấy tiến độ học tập của lớp (có thể mở rộng sau)"""
        return {
            'total_students': self.current_students,
            'max_students': self.max_students,
            'completion_rate': (self.current_students / self.max_students * 100) if self.max_students > 0 else 0,
            'status': self.status
        }
    
    @classmethod
    def get_classes_by_year(cls, year):
        """Lấy tất cả lớp theo năm học"""
        return cls.objects.filter(academic_year=year, status='active')
    
    @classmethod
    def get_classes_by_department(cls, department):
        """Lấy tất cả lớp theo khoa"""
        return cls.objects.filter(department=department, status='active')
    
    @classmethod
    def get_active_classes(cls):
        """Lấy tất cả lớp đang hoạt động"""
        return cls.objects.filter(status='active')
    
    @classmethod
    def get_graduated_classes(cls):
        """Lấy tất cả lớp đã tốt nghiệp"""
        return cls.objects.filter(status='graduated')
    
    @property
    def short_name(self):
        """Tên ngắn gọn của lớp"""
        return self.name
    
    @property
    def full_name(self):
        """Tên đầy đủ của lớp"""
        return self.display_name
    
    @property
    def department_name(self):
        """Tên khoa/ngành"""
        return self.get_department_display()
    
    @property
    def year_display(self):
        """Hiển thị năm học"""
        return f"K{self.academic_year}" 