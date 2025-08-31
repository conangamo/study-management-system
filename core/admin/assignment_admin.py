"""
Admin configuration for Assignment models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone

from ..models.assignment import Assignment, AssignmentFile, AssignmentSubmission, AssignmentGrade


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin cho Assignment model"""
    
    list_display = [
        'title', 'course', 'created_by', 'status', 'due_date', 
        'submission_count', 'graded_count', 'is_overdue_display'
    ]
    list_filter = [
        'status', 'course', 'created_by', 'allow_late_submission',
        'is_visible_to_students', 'created_at', 'due_date'
    ]
    search_fields = ['title', 'description', 'course__name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'submission_count', 'graded_count']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('course', 'title', 'description', 'instructions')
        }),
        ('Cài đặt bài tập', {
            'fields': ('due_date', 'max_score', 'status', 'is_visible_to_students')
        }),
        ('Cài đặt file', {
            'fields': ('allow_late_submission', 'max_file_size', 'allowed_file_types')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Override queryset để thêm annotations"""
        qs = super().get_queryset(request)
        return qs.select_related('course', 'created_by').annotate(
            submission_count=Count('submissions'),
            graded_count=Count('submissions', filter=Q(submissions__status='graded'))
        )
    
    def submission_count(self, obj):
        """Hiển thị số lượng bài nộp"""
        return obj.submission_count
    submission_count.short_description = 'Số bài nộp'
    submission_count.admin_order_field = 'submission_count'
    
    def graded_count(self, obj):
        """Hiển thị số lượng bài đã chấm"""
        return obj.graded_count
    graded_count.short_description = 'Đã chấm'
    graded_count.admin_order_field = 'graded_count'
    
    def is_overdue_display(self, obj):
        """Hiển thị trạng thái quá hạn"""
        if obj.is_overdue:
            return format_html('<span style="color: red;">Quá hạn</span>')
        return format_html('<span style="color: green;">Còn hạn</span>')
    is_overdue_display.short_description = 'Trạng thái hạn'
    
    def save_model(self, request, obj, form, change):
        """Override save để tự động set created_by"""
        if not change:  # Chỉ khi tạo mới
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Set readonly fields"""
        if obj:  # Khi edit
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields


@admin.register(AssignmentFile)
class AssignmentFileAdmin(admin.ModelAdmin):
    """Admin cho AssignmentFile model"""
    
    list_display = [
        'file_name', 'assignment', 'uploaded_by', 'file_type', 
        'file_size_mb', 'is_submission_file', 'uploaded_at'
    ]
    list_filter = [
        'file_type', 'is_submission_file', 'uploaded_by', 
        'assignment__course', 'uploaded_at'
    ]
    search_fields = [
        'file_name', 'assignment__title', 'uploaded_by__username'
    ]
    readonly_fields = ['file_size', 'uploaded_at', 'file_size_mb']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Thông tin file', {
            'fields': ('assignment', 'file', 'file_name', 'description')
        }),
        ('Thông tin hệ thống', {
            'fields': ('file_type', 'file_size', 'file_size_mb', 'is_submission_file')
        }),
        ('Thông tin upload', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Override queryset để thêm select_related"""
        return super().get_queryset(request).select_related(
            'assignment', 'uploaded_by'
        )
    
    def file_size_mb(self, obj):
        """Hiển thị kích thước file tính bằng MB"""
        return f"{obj.file_size_mb} MB"
    file_size_mb.short_description = 'Kích thước (MB)'
    
    def save_model(self, request, obj, form, change):
        """Override save để tự động set uploaded_by"""
        if not change:  # Chỉ khi tạo mới
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Set readonly fields"""
        if obj:  # Khi edit
            return self.readonly_fields + ('uploaded_by',)
        return self.readonly_fields


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    """Admin cho AssignmentSubmission model"""
    
    list_display = [
        'student', 'assignment', 'status', 'submitted_at', 
        'grade', 'grade_percentage', 'is_late_display'
    ]
    list_filter = [
        'status', 'assignment__course', 'assignment', 
        'submitted_at', 'graded_at'
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'assignment__title'
    ]
    readonly_fields = ['submitted_at', 'grade_percentage', 'is_late']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Thông tin bài nộp', {
            'fields': ('assignment', 'student', 'status', 'comments')
        }),
        ('Điểm số', {
            'fields': ('grade', 'feedback', 'grade_percentage')
        }),
        ('Thông tin hệ thống', {
            'fields': ('submitted_at', 'graded_by', 'graded_at', 'is_late'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Override queryset để thêm select_related"""
        return super().get_queryset(request).select_related(
            'assignment', 'student', 'graded_by'
        )
    
    def grade_percentage(self, obj):
        """Hiển thị phần trăm điểm"""
        if obj.grade_percentage > 0:
            return f"{obj.grade_percentage}%"
        return "-"
    grade_percentage.short_description = 'Phần trăm'
    
    def is_late_display(self, obj):
        """Hiển thị trạng thái nộp muộn"""
        if obj.is_late:
            return format_html('<span style="color: red;">Nộp muộn</span>')
        return format_html('<span style="color: green;">Đúng hạn</span>')
    is_late_display.short_description = 'Trạng thái nộp'
    
    def save_model(self, request, obj, form, change):
        """Override save để tự động set graded_by"""
        if obj.grade and not obj.graded_by:
            obj.graded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Set readonly fields"""
        if obj:  # Khi edit
            return self.readonly_fields + ('student', 'assignment')
        return self.readonly_fields


@admin.register(AssignmentGrade)
class AssignmentGradeAdmin(admin.ModelAdmin):
    """Admin cho AssignmentGrade model"""
    
    list_display = [
        'submission', 'score', 'grade_percentage', 'grade_letter',
        'graded_by', 'graded_at', 'is_final'
    ]
    list_filter = [
        'is_final', 'graded_by', 'graded_at',
        'submission__assignment__course'
    ]
    search_fields = [
        'submission__student__username',
        'submission__assignment__title',
        'graded_by__username'
    ]
    readonly_fields = ['graded_at', 'grade_percentage', 'grade_letter']
    date_hierarchy = 'graded_at'
    
    fieldsets = (
        ('Thông tin điểm', {
            'fields': ('submission', 'score', 'feedback', 'is_final')
        }),
        ('Điểm chi tiết', {
            'fields': ('criteria_scores', 'rubric_used'),
            'classes': ('collapse',)
        }),
        ('Thông tin chấm điểm', {
            'fields': ('graded_by', 'graded_at', 'grade_percentage', 'grade_letter'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Override queryset để thêm select_related"""
        return super().get_queryset(request).select_related(
            'submission__student', 'submission__assignment', 'graded_by'
        )
    
    def grade_percentage(self, obj):
        """Hiển thị phần trăm điểm"""
        return f"{obj.grade_percentage}%"
    grade_percentage.short_description = 'Phần trăm'
    
    def grade_letter(self, obj):
        """Hiển thị điểm chữ cái"""
        return obj.grade_letter
    grade_letter.short_description = 'Điểm chữ'
    
    def save_model(self, request, obj, form, change):
        """Override save để tự động set graded_by"""
        if not change:  # Chỉ khi tạo mới
            obj.graded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Set readonly fields"""
        if obj:  # Khi edit
            return self.readonly_fields + ('graded_by',)
        return self.readonly_fields 