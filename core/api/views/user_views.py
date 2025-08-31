"""
User API Views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from core.models import UserProfile, UserRole, StudentAccountRequest
from ..serializers import (
    UserSerializer, UserCreateSerializer, UserProfileSerializer,
    UserRoleSerializer, StudentAccountRequestSerializer,
    StudentAccountRequestCreateSerializer, PasswordChangeSerializer
)
from ..permissions import IsAdminOnly, IsTeacherOrAdmin


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view với rate limiting"""
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserListCreateView(generics.ListCreateAPIView):
    """
    List users hoặc tạo user mới
    Chỉ admin mới có thể tạo user
    """
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminOnly()]
        return [permissions.IsAuthenticated()]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Xem, cập nhật hoặc xóa user
    """
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminOnly()]
        return [permissions.IsAuthenticated()]


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Xem và cập nhật thông tin user hiện tại
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Cập nhật profile của user hiện tại
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile


class PasswordChangeView(APIView):
    """
    Đổi mật khẩu
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='3/m', method='POST'))
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Cập nhật session để không bị logout
            update_session_auth_hash(request, user)
            
            return Response({
                'message': 'Đổi mật khẩu thành công.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRoleListCreateView(generics.ListCreateAPIView):
    """
    List và tạo user roles
    """
    queryset = UserRole.objects.select_related('user').all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdminOnly]


class UserRoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa user role
    """
    queryset = UserRole.objects.select_related('user').all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdminOnly]


class StudentAccountRequestListCreateView(generics.ListCreateAPIView):
    """
    List và tạo student account requests
    """
    queryset = StudentAccountRequest.objects.select_related(
        'requested_by', 'created_user'
    ).all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentAccountRequestCreateSerializer
        return StudentAccountRequestSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]


class StudentAccountRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa student account request
    """
    queryset = StudentAccountRequest.objects.select_related(
        'requested_by', 'created_user'
    ).all()
    serializer_class = StudentAccountRequestSerializer
    permission_classes = [IsTeacherOrAdmin]


@api_view(['POST'])
@permission_classes([IsAdminOnly])
def approve_student_request(request, pk):
    """
    Duyệt yêu cầu tạo tài khoản sinh viên
    """
    try:
        request_obj = StudentAccountRequest.objects.get(pk=pk)
        
        if request_obj.status != 'pending':
            return Response({
                'error': 'Yêu cầu này đã được xử lý.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo user mới
        username = request_obj.student_id
        email = request_obj.email
        
        # Kiểm tra trùng lặp
        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'Username đã tồn tại.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email đã tồn tại.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=request_obj.first_name,
            last_name=request_obj.last_name,
            password=username  # Mật khẩu mặc định là username
        )
        
        # Cập nhật profile
        profile = user.profile
        profile.role = 'student'
        profile.student_id = request_obj.student_id
        profile.department = request_obj.department
        profile.year_of_study = request_obj.year_of_study
        profile.phone = request_obj.phone
        profile.created_by = request.user
        profile.save()
        
        # Cập nhật request
        request_obj.approve(request.user)
        request_obj.complete(user)
        
        return Response({
            'message': 'Duyệt yêu cầu thành công.',
            'user_id': user.id,
            'username': user.username,
            'default_password': username
        }, status=status.HTTP_200_OK)
        
    except StudentAccountRequest.DoesNotExist:
        return Response({
            'error': 'Không tìm thấy yêu cầu.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminOnly])
def reject_student_request(request, pk):
    """
    Từ chối yêu cầu tạo tài khoản sinh viên
    """
    try:
        request_obj = StudentAccountRequest.objects.get(pk=pk)
        
        if request_obj.status != 'pending':
            return Response({
                'error': 'Yêu cầu này đã được xử lý.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')
        request_obj.reject(request.user, reason)
        
        return Response({
            'message': 'Từ chối yêu cầu thành công.'
        }, status=status.HTTP_200_OK)
        
    except StudentAccountRequest.DoesNotExist:
        return Response({
            'error': 'Không tìm thấy yêu cầu.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """
    Thống kê người dùng
    """
    if not request.user.profile.role == 'admin':
        return Response({
            'error': 'Không có quyền truy cập.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_users': User.objects.count(),
        'students': User.objects.filter(profile__role='student').count(),
        'teachers': User.objects.filter(profile__role='teacher').count(),
        'admins': User.objects.filter(profile__role='admin').count(),
        'verified_users': User.objects.filter(profile__is_verified=True).count(),
        'pending_requests': StudentAccountRequest.objects.filter(status='pending').count(),
    }
    
    return Response(stats) 