"""
Admin for request models
"""
from django.contrib import admin
from core.models import StudentAccountRequest


@admin.register(StudentAccountRequest)
class StudentAccountRequestAdmin(admin.ModelAdmin):
    """Admin cho StudentAccountRequest với chức năng nâng cao"""
    list_display = ('student_id', 'full_name', 'email', 'department', 'year_of_study', 'status', 'requested_by', 'created_at')
    list_filter = ('status', 'department', 'year_of_study', 'created_at')
    search_fields = ('student_id', 'first_name', 'last_name', 'email', 'requested_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin sinh viên', {
            'fields': ('student_id', 'email', 'first_name', 'last_name', 'department', 'year_of_study', 'phone')
        }),
        ('Yêu cầu', {
            'fields': ('requested_by', 'status', 'notes')
        }),
        ('Tài khoản được tạo', {
            'fields': ('created_user',),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def full_name(self, obj):
        """Hiển thị họ tên đầy đủ"""
        return obj.full_name
    full_name.short_description = 'Họ tên'
    
    def approve_requests(self, request, queryset):
        """Duyệt các yêu cầu đã chọn"""
        updated = queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f'Đã duyệt {updated} yêu cầu.')
    approve_requests.short_description = 'Duyệt các yêu cầu đã chọn'
    
    def reject_requests(self, request, queryset):
        """Từ chối các yêu cầu đã chọn"""
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'Đã từ chối {updated} yêu cầu.')
    reject_requests.short_description = 'Từ chối các yêu cầu đã chọn'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requested_by', 'created_user') 