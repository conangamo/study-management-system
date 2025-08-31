"""
Admin for user models
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from core.models import UserProfile, UserRole


class UserProfileInline(admin.StackedInline):
    """Inline cho UserProfile trong User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Thông tin cá nhân'
    fields = ('role', 'phone', 'student_id', 'department', 'year_of_study', 'avatar', 'bio', 'is_verified', 'created_by')
    fk_name = 'user'


class UserRoleInline(admin.TabularInline):
    """Inline cho UserRole trong User admin"""
    model = UserRole
    extra = 0
    verbose_name_plural = 'Vai trò'


class UserAdmin(BaseUserAdmin):
    """Custom User Admin với chức năng quản lý nâng cao"""
    inlines = [UserProfileInline, UserRoleInline]
    list_display = ('username', 'email', 'full_name', 'role', 'student_id', 'is_active', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'profile__role', 'profile__department', 'profile__is_verified', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__student_id')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    list_per_page = 25
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('first_name', 'last_name', 'email')}),
        ('Quyền hạn', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Quan trọng', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    actions = ['activate_users', 'deactivate_users', 'reset_passwords']
    
    def full_name(self, obj):
        """Hiển thị họ tên đầy đủ"""
        return obj.get_full_name() or obj.username
    full_name.short_description = 'Họ tên'
    
    def role(self, obj):
        """Hiển thị vai trò"""
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return 'Chưa có'
    role.short_description = 'Vai trò'
    
    def student_id(self, obj):
        """Hiển thị mã sinh viên"""
        if hasattr(obj, 'profile') and obj.profile.student_id:
            return obj.profile.student_id
        return '-'
    student_id.short_description = 'Mã sinh viên'
    
    def activate_users(self, request, queryset):
        """Kích hoạt người dùng"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Đã kích hoạt {updated} người dùng.')
    activate_users.short_description = 'Kích hoạt người dùng đã chọn'
    
    def deactivate_users(self, request, queryset):
        """Vô hiệu hóa người dùng"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Đã vô hiệu hóa {updated} người dùng.')
    deactivate_users.short_description = 'Vô hiệu hóa người dùng đã chọn'
    
    def reset_passwords(self, request, queryset):
        """Reset mật khẩu về username"""
        count = 0
        for user in queryset:
            user.set_password(user.username)
            user.save()
            count += 1
        self.message_user(request, f'Đã reset mật khẩu cho {count} người dùng.')
    reset_passwords.short_description = 'Reset mật khẩu về username'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin cho UserProfile"""
    list_display = ('user', 'role', 'student_id', 'department', 'year_of_study', 'is_verified', 'created_by', 'created_at')
    list_filter = ('role', 'department', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'student_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin người dùng', {
            'fields': ('user', 'role')
        }),
        ('Thông tin cá nhân', {
            'fields': ('phone', 'student_id', 'department', 'year_of_study', 'avatar', 'bio')
        }),
        ('Trạng thái', {
            'fields': ('is_verified', 'created_by')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_profiles', 'unverify_profiles']
    
    def verify_profiles(self, request, queryset):
        """Xác thực profiles"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'Đã xác thực {updated} profile.')
    verify_profiles.short_description = 'Xác thực profiles đã chọn'
    
    def unverify_profiles(self, request, queryset):
        """Bỏ xác thực profiles"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'Đã bỏ xác thực {updated} profile.')
    unverify_profiles.short_description = 'Bỏ xác thực profiles đã chọn'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'created_by')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin cho UserRole"""
    list_display = ('user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user') 