from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.db import transaction
import logging
from django.db import models

from .models import UserProfile, LoginHistory, PasswordReset, AccountLockout, StudentAccountRequest
from .serializers import (
    LoginSerializer, UserSerializer, UserProfileSerializer,
    PasswordChangeSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer, UserProfileUpdateSerializer,
    LoginHistorySerializer, AdminUserSerializer, StudentAccountRequestSerializer,
    StudentAccountRequestActionSerializer
)

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """View cho đăng nhập"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Đăng nhập người dùng"""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            remember_me = serializer.validated_data.get('remember_me', False)
            
            # Kiểm tra account lockout
            ip_address = self.get_client_ip(request)
            lockout = AccountLockout.objects.filter(
                user__email=email,
                ip_address=ip_address
            ).first()
            
            if lockout and lockout.is_locked():
                return Response({
                    'error': 'Tài khoản đã bị khóa do đăng nhập sai nhiều lần. Vui lòng thử lại sau 30 phút.'
                }, status=status.HTTP_423_LOCKED)
            
            # Xác thực user bằng email
            user = authenticate(request, username=email, password=password)
            
            if user is not None and user.is_active:
                # Reset failed attempts nếu đăng nhập thành công
                if lockout:
                    lockout.reset_failed_attempts()
                
                # Login - this will create a new session
                login(request, user)
                
                # Cập nhật last_login
                user.last_login = timezone.now()
                user.save()
                
                # Tạo login history
                LoginHistory.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=True
                )
                
                # Set session type and path for user
                request.session['session_type'] = 'user'
                request.session['session_path'] = '/'
                request.session['user_id'] = user.id
                request.session['user_role'] = user.profile.role
                
                # Ensure session is saved
                request.session.save()
                
                response = Response({
                    'message': 'Đăng nhập thành công!',
                    'user': UserSerializer(user).data,
                    'profile': UserProfileSerializer(user.profile).data,
                    'session_info': {
                        'session_key': request.session.session_key,
                        'session_type': 'user',
                        'user_id': user.id,
                        'user_role': user.profile.role
                    }
                }, status=status.HTTP_200_OK)
                
                # Manually set session cookie for API response
                if request.session.session_key:
                    response.set_cookie(
                        'sessionid',
                        request.session.session_key,
                        max_age=settings.SESSION_COOKIE_AGE,
                        httponly=True,
                        secure=settings.SESSION_COOKIE_SECURE,
                        samesite=settings.SESSION_COOKIE_SAMESITE
                    )
                
                return response
            
            else:
                # Ghi nhận lần đăng nhập thất bại
                try:
                    user = User.objects.get(email=email)
                    if user.is_active:
                        # Tạo hoặc cập nhật lockout
                        lockout, created = AccountLockout.objects.get_or_create(
                            user=user,
                            ip_address=ip_address,
                            defaults={'failed_attempts': 0}
                        )
                        lockout.increment_failed_attempts()
                        
                        # Tạo login history cho lần thất bại
                        LoginHistory.objects.create(
                            user=user,
                            ip_address=ip_address,
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            success=False,
                            failure_reason='Sai mật khẩu'
                        )
                except User.DoesNotExist:
                    pass
                
                return Response({
                    'error': 'Email hoặc mật khẩu không đúng.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Lấy IP của client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """View cho đăng xuất user"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Đăng xuất người dùng - chỉ ảnh hưởng đến user session"""
        try:
            # Only logout if this is a user session
            if request.session.get('session_type') == 'user':
                # Cập nhật logout time cho login history gần nhất
                latest_login = LoginHistory.objects.filter(
                    user=request.user,
                    success=True,
                    logout_time__isnull=True
                ).order_by('-login_time').first()
                
                if latest_login:
                    latest_login.logout_time = timezone.now()
                    latest_login.save()
                
                # Logout user session
                logout(request)
                
                # Create response with cookie deletion
                from rest_framework.response import Response
                response = Response({
                    'message': 'Đăng xuất thành công!'
                }, status=status.HTTP_200_OK)
                
                # Delete user session cookie
                response.delete_cookie('user_sessionid', path='/')
                response.delete_cookie('sessionid', path='/')
                
                return response
            else:
                return Response({
                    'message': 'Bạn không có phiên user để đăng xuất.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Lỗi đăng xuất: {str(e)}")
            return Response({
                'error': 'Có lỗi xảy ra khi đăng xuất.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    """View cho thông tin cá nhân"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy thông tin cá nhân"""
        user = request.user
        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(user.profile).data
        })
    
    def put(self, request):
        """Cập nhật thông tin cá nhân"""
        profile = request.user.profile
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Cập nhật thông tin thành công!',
                'profile': UserProfileSerializer(profile).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """View cho đổi mật khẩu"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Đổi mật khẩu"""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            
            # Đổi mật khẩu
            user.set_password(new_password)
            user.save()
            
            # Logout user để yêu cầu đăng nhập lại
            logout(request)
            
            return Response({
                'message': 'Đổi mật khẩu thành công! Vui lòng đăng nhập lại.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """View cho yêu cầu đặt lại mật khẩu"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Gửi yêu cầu đặt lại mật khẩu"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Tạo token
            token = get_random_string(64)
            expires_at = timezone.now() + timezone.timedelta(hours=24)
            
            # Lưu password reset
            PasswordReset.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Gửi email
            self.send_password_reset_email(user, token)
            
            return Response({
                'message': 'Email đặt lại mật khẩu đã được gửi!'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_password_reset_email(self, user, token):
        """Gửi email đặt lại mật khẩu"""
        try:
            subject = 'Đặt lại mật khẩu - Hệ thống Quản lý Học tập'
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            message = f"""
            Xin chào {user.get_full_name()}!
            
            Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản {user.username}.
            
            Vui lòng click vào link sau để đặt lại mật khẩu:
            {reset_url}
            
            Link này có hiệu lực trong 24 giờ.
            
            Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.
            
            Trân trọng,
            Đội ngũ phát triển
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Lỗi gửi email đặt lại mật khẩu: {str(e)}")


class PasswordResetConfirmView(APIView):
    """View cho xác nhận đặt lại mật khẩu"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Xác nhận đặt lại mật khẩu"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            password_reset = serializer.validated_data['password_reset']
            new_password = serializer.validated_data['new_password']
            
            # Đặt lại mật khẩu
            user = password_reset.user
            user.set_password(new_password)
            user.save()
            
            # Đánh dấu token đã sử dụng
            password_reset.used = True
            password_reset.save()
            
            return Response({
                'message': 'Đặt lại mật khẩu thành công!'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginHistoryView(generics.ListAPIView):
    """View cho lịch sử đăng nhập"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoginHistorySerializer
    
    def get_queryset(self):
        """Lấy lịch sử đăng nhập của user hiện tại"""
        return LoginHistory.objects.filter(user=self.request.user)


class StudentAccountRequestView(generics.ListCreateAPIView):
    """View cho quản lý yêu cầu tạo tài khoản sinh viên"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentAccountRequestSerializer
    
    def get_queryset(self):
        """Lấy danh sách yêu cầu theo quyền"""
        user = self.request.user
        
        if user.profile.is_admin:
            # Admin thấy tất cả yêu cầu
            return StudentAccountRequest.objects.all()
        elif user.profile.is_teacher:
            # Teacher thấy yêu cầu của mình và yêu cầu chờ xử lý
            return StudentAccountRequest.objects.filter(
                models.Q(requested_by=user) | models.Q(status='pending')
            )
        else:
            # Student chỉ thấy yêu cầu của mình
            return StudentAccountRequest.objects.filter(requested_by=user)
    
    def perform_create(self, serializer):
        """Tạo yêu cầu mới"""
        serializer.save(requested_by=self.request.user)


class StudentAccountRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View cho xem/sửa/xóa yêu cầu tạo tài khoản sinh viên"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentAccountRequestSerializer
    queryset = StudentAccountRequest.objects.all()
    
    def get_queryset(self):
        """Lấy queryset theo quyền"""
        user = self.request.user
        
        if user.profile.is_admin:
            return StudentAccountRequest.objects.all()
        elif user.profile.is_teacher:
            return StudentAccountRequest.objects.filter(
                models.Q(requested_by=user) | models.Q(status='pending')
            )
        else:
            return StudentAccountRequest.objects.filter(requested_by=user)


class StudentAccountRequestActionView(APIView):
    """View cho duyệt/từ chối yêu cầu tạo tài khoản sinh viên"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, request_id):
        """Xử lý hành động duyệt/từ chối"""
        # Kiểm tra quyền
        if not request.user.profile.can_create_student_accounts:
            return Response({
                'error': 'Bạn không có quyền xử lý yêu cầu này.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Lấy yêu cầu
        try:
            student_request = StudentAccountRequest.objects.get(id=request_id)
        except StudentAccountRequest.DoesNotExist:
            return Response({
                'error': 'Yêu cầu không tồn tại.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Kiểm tra trạng thái
        if student_request.status != 'pending':
            return Response({
                'error': 'Yêu cầu này đã được xử lý.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = StudentAccountRequestActionSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            notes = serializer.validated_data.get('notes', '')
            
            try:
                with transaction.atomic():
                    if action == 'approve':
                        # Duyệt yêu cầu
                        student_request.approve(request.user)
                        
                        # Tạo tài khoản sinh viên
                        username = f"sv{student_request.student_id}"
                        password = get_random_string(12)  # Tạo mật khẩu ngẫu nhiên
                        
                        user = User.objects.create_user(
                            username=username,
                            email=student_request.email,
                            password=password,
                            first_name=student_request.first_name,
                            last_name=student_request.last_name,
                            is_active=True
                        )
                        
                        # Cập nhật profile
                        profile = user.profile
                        profile.role = 'student'
                        profile.student_id = student_request.student_id
                        profile.department = student_request.department
                        profile.year_of_study = student_request.year_of_study
                        profile.phone = student_request.phone
                        profile.is_verified = True
                        profile.created_by = request.user
                        profile.save()
                        
                        # Cập nhật trạng thái yêu cầu
                        student_request.complete(user)
                        
                        # Gửi email thông báo
                        self.send_account_created_email(user, request.user, password)
                        
                        return Response({
                            'message': 'Đã duyệt và tạo tài khoản thành công!',
                            'user': UserSerializer(user).data,
                            'profile': UserProfileSerializer(user.profile).data,
                            'password': password  # Chỉ trả về cho admin/teacher
                        }, status=status.HTTP_200_OK)
                    
                    elif action == 'reject':
                        # Từ chối yêu cầu
                        student_request.reject(request.user, notes)
                        
                        return Response({
                            'message': 'Đã từ chối yêu cầu.'
                        }, status=status.HTTP_200_OK)
                        
            except Exception as e:
                logger.error(f"Lỗi xử lý yêu cầu: {str(e)}")
                return Response({
                    'error': 'Có lỗi xảy ra khi xử lý yêu cầu.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_account_created_email(self, new_user, created_by, password):
        """Gửi email thông báo tài khoản được tạo"""
        try:
            subject = 'Tài khoản sinh viên đã được tạo - Hệ thống Quản lý Học tập'
            message = f"""
            Xin chào {new_user.get_full_name()}!
            
            Tài khoản sinh viên của bạn đã được tạo bởi {created_by.get_full_name()} ({created_by.profile.get_role_display()}).
            
            Thông tin tài khoản:
            - Tên đăng nhập: {new_user.username}
            - Email: {new_user.email}
            - Mật khẩu: {password}
            - Mã sinh viên: {new_user.profile.student_id}
            - Khoa/Ngành: {new_user.profile.get_department_display()}
            - Năm học: {new_user.profile.year_of_study}
            
            Vui lòng đăng nhập và đổi mật khẩu ngay để bảo mật tài khoản.
            
            Trân trọng,
            Đội ngũ phát triển
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [new_user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Lỗi gửi email: {str(e)}")


# Admin Views
class AdminUserListView(generics.ListCreateAPIView):
    """View cho admin quản lý users"""
    
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all().order_by('-date_joined')


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View cho admin xem/sửa/xóa user"""
    
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_toggle_user_status(request, user_id):
    """Admin toggle trạng thái active của user"""
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_text = "kích hoạt" if user.is_active else "vô hiệu hóa"
        
        return Response({
            'message': f'Đã {status_text} tài khoản {user.username}!'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Lỗi toggle user status: {str(e)}")
        return Response({
            'error': 'Có lỗi xảy ra!'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 