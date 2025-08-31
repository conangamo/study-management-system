"""
User API Serializers
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import UserProfile, UserRole, StudentAccountRequest


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer cho UserProfile"""
    full_name = serializers.ReadOnlyField()
    is_student = serializers.ReadOnlyField()
    is_teacher = serializers.ReadOnlyField()
    is_admin = serializers.ReadOnlyField()
    can_create_student_accounts = serializers.ReadOnlyField()
    can_manage_users = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'role', 'phone', 'student_id', 'department', 
            'year_of_study', 'avatar', 'bio', 'is_verified',
            'created_at', 'updated_at', 'full_name', 'is_student',
            'is_teacher', 'is_admin', 'can_create_student_accounts',
            'can_manage_users'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_verified']


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho User với profile"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer để tạo user mới"""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    profile_data = UserProfileSerializer(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'profile_data'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Mật khẩu không khớp.")
        return attrs
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile_data', {})
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(**validated_data)
        
        # Cập nhật profile nếu có
        if profile_data:
            profile = user.profile
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save()
        
        return user


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer cho UserRole"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_username', 'role', 'role_display', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class StudentAccountRequestSerializer(serializers.ModelSerializer):
    """Serializer cho StudentAccountRequest"""
    full_name = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    created_user_name = serializers.CharField(source='created_user.get_full_name', read_only=True)
    
    class Meta:
        model = StudentAccountRequest
        fields = [
            'id', 'student_id', 'email', 'first_name', 'last_name', 
            'full_name', 'department', 'department_display', 'year_of_study', 
            'phone', 'status', 'status_display', 'notes',
            'requested_by', 'requested_by_name', 'created_user', 'created_user_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_user']


class StudentAccountRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer để tạo yêu cầu tài khoản sinh viên"""
    
    class Meta:
        model = StudentAccountRequest
        fields = [
            'student_id', 'email', 'first_name', 'last_name',
            'department', 'year_of_study', 'phone', 'notes'
        ]
    
    def create(self, validated_data):
        # Tự động set requested_by từ request user
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer để đổi mật khẩu"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Mật khẩu mới không khớp.")
        
        # Kiểm tra mật khẩu cũ
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError("Mật khẩu cũ không đúng.")
        
        return attrs 