"""
Admin configuration cho Study Management Models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages

from .models import Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, Tag, Note


class CourseEnrollmentInline(admin.TabularInline):
    """Inline cho CourseEnrollment trong Course admin"""
    model = CourseEnrollment
    extra = 0
    verbose_name_plural = 'Sinh viên đăng ký'
    fields = ('student', 'status', 'enrolled_at', 'final_grade')
    readonly_fields = ('enrolled_at',)


class AssignmentInline(admin.TabularInline):
    """Inline cho Assignment trong Course admin"""
    model = Assignment
    extra = 0
    verbose_name_plural = 'Bài tập'
    fields = ('title', 'assignment_type', 'due_date', 'status', 'max_score')
    readonly_fields = ('created_at',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin cho Course với chức năng quản lý nâng cao"""
    list_display = ('code', 'name', 'teacher', 'semester', 'academic_year', 'status', 'student_count', 'is_active', 'created_at')
    list_filter = ('status', 'semester', 'academic_year', 'teacher__profile__department', 'created_at')
    search_fields = ('code', 'name', 'teacher__username', 'teacher__first_name', 'teacher__last_name')
    ordering = ('-academic_year', 'semester', 'name')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'code', 'description', 'credits')
        }),
        ('Thời gian', {
            'fields': ('semester', 'academic_year', 'start_date', 'end_date')
        }),
        ('Giảng viên và sinh viên', {
            'fields': ('teacher', 'max_students')
        }),
        ('Trạng thái', {
            'fields': ('status', 'syllabus')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CourseEnrollmentInline, AssignmentInline]
    
    actions = ['activate_courses', 'complete_courses', 'archive_courses']
    
    def student_count(self, obj):
        """Số lượng sinh viên đăng ký"""
        return obj.enrolled_student_count
    student_count.short_description = 'Số SV'
    
    def is_active(self, obj):
        """Kiểm tra môn học có đang diễn ra không"""
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Đang diễn ra'
    
    def activate_courses(self, request, queryset):
        """Kích hoạt các khóa học được chọn"""
        updated = queryset.update(status='active')
        self.message_user(request, f'Đã kích hoạt {updated} khóa học.')
    activate_courses.short_description = 'Kích hoạt khóa học'
    
    def complete_courses(self, request, queryset):
        """Hoàn thành các khóa học được chọn"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'Đã hoàn thành {updated} khóa học.')
    complete_courses.short_description = 'Hoàn thành khóa học'
    
    def archive_courses(self, request, queryset):
        """Lưu trữ các khóa học được chọn"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'Đã lưu trữ {updated} khóa học.')
    archive_courses.short_description = 'Lưu trữ khóa học'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('teacher').prefetch_related('students')


class AssignmentSubmissionInline(admin.TabularInline):
    """Inline cho AssignmentSubmission trong Assignment admin"""
    model = AssignmentSubmission
    extra = 0
    verbose_name_plural = 'Bài nộp'
    fields = ('student', 'status', 'submitted_at', 'score', 'is_late')
    readonly_fields = ('submitted_at', 'is_late')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin cho Assignment với chức năng quản lý nâng cao"""
    list_display = ('title', 'course', 'assignment_type', 'due_date', 'status', 'submission_count', 'graded_count', 'is_overdue', 'created_by')
    list_filter = ('status', 'assignment_type', 'priority', 'course__semester', 'course__academic_year', 'created_at')
    search_fields = ('title', 'course__name', 'course__code', 'created_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'description', 'course', 'assignment_type', 'priority')
        }),
        ('Thời gian', {
            'fields': ('due_date', 'submission_deadline', 'allow_late_submission')
        }),
        ('Điểm số', {
            'fields': ('max_score', 'weight')
        }),
        ('Cài đặt', {
            'fields': ('status', 'max_submissions', 'is_anonymous', 'attachment')
        }),
        ('Thông tin tạo', {
            'fields': ('created_by', 'created_at', 'published_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AssignmentSubmissionInline]
    
    actions = ['publish_assignments', 'open_submissions', 'close_submissions', 'archive_assignments']
    
    def submission_count(self, obj):
        """Số lượng bài nộp"""
        return obj.submission_count
    submission_count.short_description = 'Bài nộp'
    
    def graded_count(self, obj):
        """Số lượng bài đã chấm điểm"""
        return obj.graded_count
    graded_count.short_description = 'Đã chấm'
    
    def is_overdue(self, obj):
        """Kiểm tra bài tập có quá hạn không"""
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Quá hạn'
    
    def publish_assignments(self, request, queryset):
        """Công bố các bài tập được chọn"""
        for assignment in queryset:
            assignment.publish()
        self.message_user(request, f'Đã công bố {queryset.count()} bài tập.')
    publish_assignments.short_description = 'Công bố bài tập'
    
    def open_submissions(self, request, queryset):
        """Mở nhận bài cho các bài tập được chọn"""
        for assignment in queryset:
            assignment.open_submission()
        self.message_user(request, f'Đã mở nhận bài cho {queryset.count()} bài tập.')
    open_submissions.short_description = 'Mở nhận bài'
    
    def close_submissions(self, request, queryset):
        """Đóng nhận bài cho các bài tập được chọn"""
        for assignment in queryset:
            assignment.close_submission()
        self.message_user(request, f'Đã đóng nhận bài cho {queryset.count()} bài tập.')
    close_submissions.short_description = 'Đóng nhận bài'
    
    def archive_assignments(self, request, queryset):
        """Lưu trữ các bài tập được chọn"""
        for assignment in queryset:
            assignment.archive()
        self.message_user(request, f'Đã lưu trữ {queryset.count()} bài tập.')
    archive_assignments.short_description = 'Lưu trữ bài tập'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('course', 'created_by')


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    """Admin cho AssignmentSubmission"""
    list_display = ('assignment', 'student', 'status', 'submitted_at', 'score', 'is_late', 'submission_number')
    list_filter = ('status', 'is_late', 'submitted_at', 'assignment__course')
    search_fields = ('assignment__title', 'student__username', 'student__first_name', 'student__last_name')
    ordering = ('-submitted_at',)
    readonly_fields = ('submitted_at', 'graded_at', 'is_late')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin bài nộp', {
            'fields': ('assignment', 'student', 'status', 'submission_number')
        }),
        ('Nội dung', {
            'fields': ('content', 'attachment')
        }),
        ('Điểm số', {
            'fields': ('score', 'feedback')
        }),
        ('Thời gian', {
            'fields': ('submitted_at', 'graded_at', 'is_late'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['grade_submissions', 'mark_as_late']
    
    def grade_submissions(self, request, queryset):
        """Chấm điểm các bài nộp được chọn"""
        # Có thể thêm form để nhập điểm hàng loạt
        self.message_user(request, f'Đã chọn {queryset.count()} bài nộp để chấm điểm.')
    grade_submissions.short_description = 'Chấm điểm bài nộp'
    
    def mark_as_late(self, request, queryset):
        """Đánh dấu bài nộp muộn"""
        updated = queryset.update(is_late=True, status='late')
        self.message_user(request, f'Đã đánh dấu {updated} bài nộp muộn.')
    mark_as_late.short_description = 'Đánh dấu nộp muộn'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('assignment', 'student')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """Admin cho Grade với chức năng quản lý nâng cao"""
    list_display = ('student', 'course', 'grade_type', 'score', 'max_score', 'percentage', 'letter_grade', 'date', 'created_by')
    list_filter = ('grade_type', 'date', 'is_final', 'course__semester', 'course__academic_year')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__name', 'course__code')
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin điểm', {
            'fields': ('student', 'course', 'assignment', 'submission', 'grade_type')
        }),
        ('Điểm số', {
            'fields': ('score', 'max_score', 'weight', 'is_final')
        }),
        ('Thông tin bổ sung', {
            'fields': ('date', 'comment')
        }),
        ('Thông tin tạo', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['calculate_averages', 'export_grades']
    
    def percentage(self, obj):
        """Hiển thị phần trăm điểm"""
        return f"{obj.percentage:.1f}%"
    percentage.short_description = 'Phần trăm'
    
    def letter_grade(self, obj):
        """Hiển thị điểm chữ"""
        return obj.letter_grade
    letter_grade.short_description = 'Điểm chữ'
    
    def calculate_averages(self, request, queryset):
        """Tính điểm trung bình cho các khóa học"""
        # Logic tính điểm trung bình
        self.message_user(request, f'Đã tính điểm trung bình cho {queryset.count()} điểm.')
    calculate_averages.short_description = 'Tính điểm trung bình'
    
    def export_grades(self, request, queryset):
        """Xuất điểm ra file"""
        # Logic xuất file
        self.message_user(request, f'Đã xuất {queryset.count()} điểm.')
    export_grades.short_description = 'Xuất điểm'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('student', 'course', 'assignment', 'created_by')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin cho Tag"""
    list_display = ('name', 'color', 'created_by', 'created_at', 'note_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'created_by__username')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin tag', {
            'fields': ('name', 'description', 'color')
        }),
        ('Thông tin tạo', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def note_count(self, obj):
        """Số lượng ghi chú sử dụng tag"""
        return obj.notes.count()
    note_count.short_description = 'Số ghi chú'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('created_by').prefetch_related('notes')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin cho Note với chức năng quản lý nâng cao"""
    list_display = ('title', 'user', 'priority', 'is_important', 'is_pinned', 'course', 'assignment', 'created_at', 'tag_list')
    list_filter = ('priority', 'is_important', 'is_pinned', 'is_public', 'created_at', 'course__semester')
    search_fields = ('title', 'content', 'user__username', 'user__first_name', 'user__last_name')
    ordering = ('-is_pinned', '-is_important', '-updated_at')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin ghi chú', {
            'fields': ('user', 'title', 'content')
        }),
        ('Thuộc tính', {
            'fields': ('priority', 'is_important', 'is_pinned', 'is_public')
        }),
        ('Liên kết', {
            'fields': ('course', 'assignment', 'tags')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('tags',)
    
    actions = ['pin_notes', 'unpin_notes', 'mark_important', 'mark_unimportant']
    
    def tag_list(self, obj):
        """Hiển thị danh sách tags"""
        return ', '.join([tag.name for tag in obj.tags.all()])
    tag_list.short_description = 'Tags'
    
    def pin_notes(self, request, queryset):
        """Ghim các ghi chú được chọn"""
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'Đã ghim {updated} ghi chú.')
    pin_notes.short_description = 'Ghim ghi chú'
    
    def unpin_notes(self, request, queryset):
        """Bỏ ghim các ghi chú được chọn"""
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'Đã bỏ ghim {updated} ghi chú.')
    unpin_notes.short_description = 'Bỏ ghim ghi chú'
    
    def mark_important(self, request, queryset):
        """Đánh dấu quan trọng"""
        updated = queryset.update(is_important=True)
        self.message_user(request, f'Đã đánh dấu {updated} ghi chú quan trọng.')
    mark_important.short_description = 'Đánh dấu quan trọng'
    
    def mark_unimportant(self, request, queryset):
        """Bỏ đánh dấu quan trọng"""
        updated = queryset.update(is_important=False)
        self.message_user(request, f'Đã bỏ đánh dấu {updated} ghi chú quan trọng.')
    mark_unimportant.short_description = 'Bỏ đánh dấu quan trọng'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user', 'course', 'assignment').prefetch_related('tags')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Admin cho CourseEnrollment"""
    list_display = ('student', 'course', 'status', 'enrolled_at', 'final_grade', 'dropped_at')
    list_filter = ('status', 'enrolled_at', 'course__semester', 'course__academic_year')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__name', 'course__code')
    ordering = ('-enrolled_at',)
    readonly_fields = ('enrolled_at', 'dropped_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin đăng ký', {
            'fields': ('student', 'course', 'status')
        }),
        ('Điểm số', {
            'fields': ('final_grade', 'notes')
        }),
        ('Thời gian', {
            'fields': ('enrolled_at', 'dropped_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['complete_enrollments', 'drop_enrollments', 'fail_enrollments']
    
    def complete_enrollments(self, request, queryset):
        """Hoàn thành các đăng ký được chọn"""
        for enrollment in queryset:
            enrollment.complete_course()
        self.message_user(request, f'Đã hoàn thành {queryset.count()} đăng ký.')
    complete_enrollments.short_description = 'Hoàn thành đăng ký'
    
    def drop_enrollments(self, request, queryset):
        """Rút các đăng ký được chọn"""
        for enrollment in queryset:
            enrollment.drop_course()
        self.message_user(request, f'Đã rút {queryset.count()} đăng ký.')
    drop_enrollments.short_description = 'Rút đăng ký'
    
    def fail_enrollments(self, request, queryset):
        """Đánh trượt các đăng ký được chọn"""
        for enrollment in queryset:
            enrollment.fail_course()
        self.message_user(request, f'Đã đánh trượt {queryset.count()} đăng ký.')
    fail_enrollments.short_description = 'Đánh trượt'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('student', 'course') 