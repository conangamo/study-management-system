"""
Admin for study management models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Avg

from core.models import Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, Tag, Note


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
    fields = ('title', 'assignment_type', 'due_date', 'status')
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
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CourseEnrollmentInline, AssignmentInline]
    actions = ['activate_courses', 'complete_courses']
    
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
        """Kích hoạt khóa học"""
        updated = queryset.update(status='active')
        self.message_user(request, f'Đã kích hoạt {updated} khóa học.')
    activate_courses.short_description = 'Kích hoạt khóa học đã chọn'
    
    def complete_courses(self, request, queryset):
        """Hoàn thành khóa học"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'Đã hoàn thành {updated} khóa học.')
    complete_courses.short_description = 'Hoàn thành khóa học đã chọn'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher').prefetch_related('students')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """Admin cho Grade với chức năng quản lý nâng cao"""
    list_display = ('student', 'course', 'grade_type', 'score', 'max_score', 'percentage', 'letter_grade', 'created_by', 'date')
    list_filter = ('grade_type', 'is_final', 'course__semester', 'course__academic_year', 'date')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__name', 'course__code')
    ordering = ('-date', 'course__name', 'student__username')
    readonly_fields = ('percentage', 'letter_grade', 'created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('student', 'course', 'assignment', 'submission')
        }),
        ('Điểm số', {
            'fields': ('grade_type', 'score', 'max_score', 'weight', 'percentage', 'letter_grade')
        }),
        ('Chi tiết', {
            'fields': ('date', 'comment', 'is_final', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_final', 'export_grades']
    
    def percentage(self, obj):
        """Hiển thị phần trăm"""
        return f"{obj.percentage:.1f}%"
    percentage.short_description = 'Phần trăm'
    
    def letter_grade(self, obj):
        """Hiển thị điểm chữ"""
        return obj.letter_grade
    letter_grade.short_description = 'Điểm chữ'
    
    def mark_as_final(self, request, queryset):
        """Đánh dấu là điểm cuối kỳ"""
        updated = queryset.update(is_final=True)
        self.message_user(request, f'Đã đánh dấu {updated} điểm là cuối kỳ.')
    mark_as_final.short_description = 'Đánh dấu là điểm cuối kỳ'
    
    def export_grades(self, request, queryset):
        """Export điểm ra Excel (placeholder)"""
        self.message_user(request, f'Export {queryset.count()} điểm (chức năng sẽ phát triển sau).')
    export_grades.short_description = 'Export điểm đã chọn'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'course', 'assignment', 'created_by')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin cho Tag"""
    list_display = ('name', 'color_display', 'note_count', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'note_count')
    
    fieldsets = (
        ('Thông tin tag', {
            'fields': ('name', 'color', 'description', 'created_by')
        }),
        ('Thống kê', {
            'fields': ('note_count',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_display(self, obj):
        """Hiển thị màu sắc"""
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Màu sắc'
    
    def note_count(self, obj):
        """Số lượng note sử dụng tag này"""
        return obj.notes.count()
    note_count.short_description = 'Số note'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').prefetch_related('notes')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Admin cho Note với chức năng quản lý nâng cao"""
    list_display = ('title', 'user', 'priority', 'is_important', 'is_pinned', 'is_public', 'course', 'tag_display', 'created_at')
    list_filter = ('priority', 'is_important', 'is_pinned', 'is_public', 'course', 'created_at')
    search_fields = ('title', 'content', 'user__username', 'course__name')
    ordering = ('-is_pinned', '-is_important', '-created_at')
    readonly_fields = ('created_at', 'updated_at', 'preview')
    list_per_page = 25
    filter_horizontal = ('tags',)
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'content', 'preview', 'user')
        }),
        ('Thuộc tính', {
            'fields': ('priority', 'is_important', 'is_pinned', 'is_public')
        }),
        ('Liên kết', {
            'fields': ('course', 'assignment', 'tags')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_important', 'mark_as_public', 'pin_notes']
    
    def preview(self, obj):
        """Xem trước nội dung"""
        return obj.preview
    preview.short_description = 'Xem trước'
    
    def tag_display(self, obj):
        """Hiển thị tags"""
        tags = obj.tags.all()[:3]  # Chỉ hiển thị 3 tag đầu
        if tags:
            tag_list = ", ".join([tag.name for tag in tags])
            if obj.tags.count() > 3:
                tag_list += f" (+{obj.tags.count()-3})"
            return tag_list
        return "-"
    tag_display.short_description = 'Tags'
    
    def mark_as_important(self, request, queryset):
        """Đánh dấu quan trọng"""
        updated = queryset.update(is_important=True)
        self.message_user(request, f'Đã đánh dấu {updated} ghi chú là quan trọng.')
    mark_as_important.short_description = 'Đánh dấu quan trọng'
    
    def mark_as_public(self, request, queryset):
        """Đánh dấu công khai"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'Đã đánh dấu {updated} ghi chú là công khai.')
    mark_as_public.short_description = 'Đánh dấu công khai'
    
    def pin_notes(self, request, queryset):
        """Ghim ghi chú"""
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'Đã ghim {updated} ghi chú.')
    pin_notes.short_description = 'Ghim ghi chú đã chọn'
    
    def get_queryset(self, request):
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
        """Hoàn thành đăng ký"""
        for enrollment in queryset:
            enrollment.complete_course()
        self.message_user(request, f'Đã hoàn thành {queryset.count()} đăng ký.')
    complete_enrollments.short_description = 'Hoàn thành đăng ký đã chọn'
    
    def drop_enrollments(self, request, queryset):
        """Rút đăng ký"""
        for enrollment in queryset:
            enrollment.drop_course()
        self.message_user(request, f'Đã rút {queryset.count()} đăng ký.')
    drop_enrollments.short_description = 'Rút đăng ký đã chọn'
    
    def fail_enrollments(self, request, queryset):
        """Trượt đăng ký"""
        for enrollment in queryset:
            enrollment.fail_course()
        self.message_user(request, f'Đã đánh dấu trượt {queryset.count()} đăng ký.')
    fail_enrollments.short_description = 'Đánh dấu trượt cho đăng ký đã chọn'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'course') 