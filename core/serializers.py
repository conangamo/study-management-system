from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, UserRole, LoginHistory, PasswordReset, StudentAccountRequest


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer cho UserProfile model"""
    
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'role', 'role_display', 'phone', 'student_id', 
            'department', 'department_display', 'year_of_study', 'avatar', 
            'bio', 'is_verified', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    """Serializer cho đăng nhập"""
    
    email = serializers.EmailField(
        label='Email',
        help_text='Nhập email của bạn'
    )
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validate dữ liệu đăng nhập"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Vui lòng nhập email và mật khẩu")
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer cho đổi mật khẩu"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate dữ liệu đổi mật khẩu"""
        user = self.context['request'].user
        
        # Kiểm tra quyền đổi mật khẩu
        if not user.profile.can_change_password:
            raise serializers.ValidationError("Bạn không có quyền đổi mật khẩu. Sinh viên cần được xác thực trước.")
        
        # Kiểm tra mật khẩu cũ
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError("Mật khẩu cũ không đúng")
        
        # Kiểm tra mật khẩu mới
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Mật khẩu mới không khớp")
        
        # Validate mật khẩu mới
        try:
            validate_password(attrs['new_password'], user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer cho yêu cầu đặt lại mật khẩu"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email tồn tại"""
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("Email không tồn tại trong hệ thống")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer cho xác nhận đặt lại mật khẩu"""
    
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate token và mật khẩu mới"""
        token = attrs['token']
        
        try:
            password_reset = PasswordReset.objects.get(token=token)
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError("Token không hợp lệ")
        
        if not password_reset.is_valid():
            raise serializers.ValidationError("Token đã hết hạn hoặc đã được sử dụng")
        
        # Kiểm tra mật khẩu mới
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Mật khẩu mới không khớp")
        
        # Validate mật khẩu mới
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        attrs['password_reset'] = password_reset
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer cho cập nhật thông tin cá nhân - chỉ cho phép chỉnh sửa phone và bio"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'phone', 'student_id', 'department', 'year_of_study', 
            'avatar', 'bio', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'student_id', 'department', 'year_of_study', 
            'avatar', 'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        """Validate chỉ cho phép cập nhật phone và bio"""
        allowed_fields = ['phone', 'bio']
        provided_fields = list(attrs.keys())
        
        # Kiểm tra xem có trường nào không được phép không
        disallowed_fields = [field for field in provided_fields if field not in allowed_fields]
        
        if disallowed_fields:
            raise serializers.ValidationError(
                f"Chỉ được phép cập nhật các trường: {', '.join(allowed_fields)}. "
                f"Các trường không được phép: {', '.join(disallowed_fields)}"
            )
        
        return attrs
    
    def update(self, instance, validated_data):
        """Override update method để chỉ cập nhật phone và bio"""
        allowed_fields = ['phone', 'bio']
        
        # Chỉ cập nhật các trường được phép
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance
    
    def to_internal_value(self, data):
        """Override để lọc ra chỉ các trường được phép"""
        allowed_fields = ['phone', 'bio']
        
        # Lọc data chỉ giữ lại các trường được phép
        filtered_data = {}
        for field in allowed_fields:
            if field in data:
                filtered_data[field] = data[field]
        
        return super().to_internal_value(filtered_data)


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer cho lịch sử đăng nhập"""
    
    user = UserSerializer(read_only=True)
    session_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'user', 'login_time', 'logout_time', 'ip_address', 
            'user_agent', 'success', 'failure_reason', 'session_duration'
        ]
        read_only_fields = ['id', 'user', 'login_time', 'logout_time', 'ip_address', 
                           'user_agent', 'success', 'failure_reason']
    
    def get_session_duration(self, obj):
        """Tính thời gian session"""
        if obj.session_duration:
            total_seconds = obj.session_duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        return None


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer cho admin quản lý users"""
    
    profile = UserProfileSerializer(read_only=True)
    is_active_display = serializers.CharField(source='get_is_active_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'is_active', 'is_active_display', 'date_joined', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login'] 


class StudentAccountRequestSerializer(serializers.ModelSerializer):
    """Serializer cho yêu cầu tạo tài khoản sinh viên"""
    
    requested_by = UserSerializer(read_only=True)
    created_user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    
    class Meta:
        model = StudentAccountRequest
        fields = [
            'id', 'student_id', 'email', 'first_name', 'last_name', 'department', 
            'department_display', 'year_of_study', 'phone', 'requested_by', 
            'created_user', 'status', 'status_display', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'requested_by', 'created_user', 'status', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate dữ liệu yêu cầu"""
        # Kiểm tra mã sinh viên đã tồn tại
        if StudentAccountRequest.objects.filter(student_id=attrs['student_id']).exists():
            raise serializers.ValidationError("Mã sinh viên đã có yêu cầu tạo tài khoản")
        
        # Kiểm tra email đã tồn tại
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email đã được sử dụng")
        
        # Kiểm tra mã sinh viên đã có tài khoản
        if UserProfile.objects.filter(student_id=attrs['student_id']).exists():
            raise serializers.ValidationError("Mã sinh viên đã có tài khoản")
        
        return attrs
    
    def create(self, validated_data):
        """Tạo yêu cầu mới"""
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)


class StudentAccountRequestActionSerializer(serializers.Serializer):
    """Serializer cho hành động duyệt/từ chối yêu cầu"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        """Validate hành động"""
        if value not in ['approve', 'reject']:
            raise serializers.ValidationError("Hành động không hợp lệ")
        return value 