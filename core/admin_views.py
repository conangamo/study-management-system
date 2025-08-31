from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
import csv
import io
from django.utils import timezone
import logging

from .models import UserProfile
# Import forms directly from core.forms
from core.forms import StudentAccountForm, TeacherAccountForm, BulkStudentAccountForm, UserSearchForm, BulkTeacherAccountForm


logger = logging.getLogger(__name__)


def is_admin(user):
    """Kiểm tra user có phải admin không"""
    if not user.is_authenticated:
        return False
    
    # Kiểm tra superuser trước
    if user.is_superuser:
        return True
    
    # Kiểm tra profile role
    if hasattr(user, 'profile') and user.profile:
        return user.profile.role == 'admin'
    
    return False


def admin_login(request):
    """Trang đăng nhập cho admin panel"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Sử dụng username để đăng nhập admin
            user = authenticate(request, username=username, password=password)
            if user is not None and is_admin(user):
                login(request, user)
                
                # Set session type for admin
                request.session['session_type'] = 'admin'
                request.session.save()
                
                next_url = request.GET.get('next', '/custom-admin/dashboard/')
                return redirect(next_url)
            else:
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng, hoặc bạn không có quyền admin.')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
    
    return render(request, 'admin/login.html')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard cho admin"""
    try:
        # Thống kê
        total_users = User.objects.count()
        students = UserProfile.objects.filter(role='student').count()
        teachers = UserProfile.objects.filter(role='teacher').count()
        admins = UserProfile.objects.filter(role='admin').count()
        
        # Thống kê môn học
        from .models.study import Course
        total_courses = Course.objects.count()
        active_courses = Course.objects.filter(status='active').count()
        
        # Thống kê lớp học
        from .models.study import Class
        total_classes = Class.objects.count()
        active_classes = Class.objects.filter(status='active').count()
        graduated_classes = Class.objects.filter(status='graduated').count()
        
        # Người dùng mới nhất
        recent_users = User.objects.select_related('profile').order_by('-date_joined')[:10]
        
        # Yêu cầu chờ xử lý
        from .models import StudentAccountRequest
        pending_requests = StudentAccountRequest.objects.filter(status='pending').count()
        
        context = {
            'total_users': total_users,
            'students': students,
            'teachers': teachers,
            'admins': admins,
            'total_courses': total_courses,
            'active_courses': active_courses,
            'total_classes': total_classes,
            'active_classes': active_classes,
            'graduated_classes': graduated_classes,
            'recent_users': recent_users,
            'pending_requests': pending_requests,
        }
        
        return render(request, 'admin/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải dashboard: {str(e)}')
        return render(request, 'admin/dashboard.html', {})


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """Danh sách người dùng với tìm kiếm và lọc"""
    try:
        form = UserSearchForm(request.GET)
        users = User.objects.select_related('profile').all()
        
        if form.is_valid():
            search_query = form.cleaned_data.get('search_query')
            role_filter = form.cleaned_data.get('role_filter')
            department_filter = form.cleaned_data.get('department_filter')
            status_filter = form.cleaned_data.get('status_filter')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            # Tìm kiếm
            if search_query:
                users = users.filter(
                    Q(username__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(profile__student_id__icontains=search_query)
                )
            
            # Lọc theo vai trò
            if role_filter:
                users = users.filter(profile__role=role_filter)
            
            # Lọc theo khoa
            if department_filter:
                users = users.filter(profile__department=department_filter)
            
            # Lọc theo trạng thái
            if status_filter:
                if status_filter == 'active':
                    users = users.filter(is_active=True)
                elif status_filter == 'inactive':
                    users = users.filter(is_active=False)
                elif status_filter == 'verified':
                    users = users.filter(profile__is_verified=True)
                elif status_filter == 'unverified':
                    users = users.filter(profile__is_verified=False)
            
            # Lọc theo ngày
            if date_from:
                users = users.filter(date_joined__gte=date_from)
            if date_to:
                users = users.filter(date_joined__lte=date_to)
        
        # Sắp xếp
        users = users.order_by('-date_joined')
        
        # Phân trang
        paginator = Paginator(users, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'form': form,
            'page_obj': page_obj,
            'users': page_obj,
        }
        
        return render(request, 'admin/user_list.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải danh sách người dùng: {str(e)}')
        return render(request, 'admin/user_list.html', {'form': form, 'users': []})


@login_required
@user_passes_test(is_admin)
def create_student_account(request):
    """Tạo tài khoản sinh viên"""
    if request.method == 'POST':
        form = StudentAccountForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Kiểm tra email đã tồn tại
                    email = form.cleaned_data['email']
                    if User.objects.filter(email=email).exists():
                        messages.error(request, 'Email này đã được sử dụng.')
                        return render(request, 'admin/create_account.html', {'form': form, 'title': 'Tạo tài khoản sinh viên'})
                    
                    # Kiểm tra student_id đã tồn tại
                    student_id = form.cleaned_data['student_id']
                    if UserProfile.objects.filter(student_id=student_id).exists():
                        messages.error(request, 'Mã sinh viên này đã tồn tại.')
                        return render(request, 'admin/create_account.html', {'form': form, 'title': 'Tạo tài khoản sinh viên'})
                    
                    # Tạo user
                    username = f"sv{student_id}"
                    
                    first_name = form.cleaned_data['first_name']
                    last_name = form.cleaned_data['last_name']
                    
                    # Tạo mật khẩu
                    if form.cleaned_data['password_option'] == 'custom':
                        password = form.cleaned_data['custom_password']
                    else:
                        password = 'Student@123'  # Mật khẩu mặc định
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                    
                    # Đảm bảo UserProfile được tạo và cập nhật
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'role': 'student',
                            'student_id': student_id,
                            'department': form.cleaned_data['department'],
                            'year_of_study': form.cleaned_data['year_of_study'],
                            'phone': form.cleaned_data.get('phone', ''),
                            'is_verified': True,
                            'created_by': request.user
                        }
                    )
                    
                    # Nếu profile đã tồn tại, cập nhật thông tin
                    if not created:
                        profile.role = 'student'
                        profile.student_id = student_id
                        profile.department = form.cleaned_data['department']
                        profile.year_of_study = form.cleaned_data['year_of_study']
                        profile.phone = form.cleaned_data.get('phone', '')
                        profile.is_verified = True
                        profile.created_by = request.user
                        profile.save()
                    
                    # Assign to class if selected
                    class_enrolled = form.cleaned_data.get('class_enrolled')
                    if class_enrolled:
                        profile.class_enrolled = class_enrolled
                        profile.save()
                        # Cập nhật sĩ số lớp
                        class_enrolled.update_student_count()
                        class_enrolled.save()
                    
                    # Gửi email
                    if form.cleaned_data.get('send_welcome_email'):
                        send_welcome_email(user, password)
                    
                    messages.success(
                        request, 
                        f'Đã tạo tài khoản sinh viên thành công!\n'
                        f'Username: {username}\n'
                        f'Mật khẩu: {password}'
                    )
                    return redirect('core:admin_user_list')
                    
            except Exception as e:
                messages.error(request, f'Lỗi tạo tài khoản: {str(e)}')
    else:
        form = StudentAccountForm()
    
    context = {
        'form': form,
        'title': 'Tạo tài khoản sinh viên',
    }
    
    return render(request, 'admin/create_account.html', context)


@login_required
@user_passes_test(is_admin)
def create_teacher_account(request):
    """Tạo tài khoản giảng viên"""
    if request.method == 'POST':
        form = TeacherAccountForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Kiểm tra email đã tồn tại
                    email = form.cleaned_data['email']
                    if User.objects.filter(email=email).exists():
                        messages.error(request, 'Email này đã được sử dụng.')
                        return render(request, 'admin/create_account.html', {'form': form, 'title': 'Tạo tài khoản giảng viên'})
                    
                    # Tạo user
                    username = f"gv{get_random_string(6).lower()}"
                    first_name = form.cleaned_data['first_name']
                    last_name = form.cleaned_data['last_name']
                    
                    # Tạo mật khẩu
                    if form.cleaned_data['password_option'] == 'custom':
                        password = form.cleaned_data['custom_password']
                    else:
                        password = 'Teacher@123'  # Mật khẩu mặc định
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                    
                    # Đảm bảo UserProfile được tạo và cập nhật
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'role': 'teacher',
                            'department': form.cleaned_data['department'],
                            'phone': form.cleaned_data.get('phone', ''),
                            'bio': form.cleaned_data.get('bio', ''),
                            'is_verified': True,
                            'created_by': request.user
                        }
                    )
                    
                    # Nếu profile đã tồn tại, cập nhật thông tin
                    if not created:
                        profile.role = 'teacher'
                        profile.department = form.cleaned_data['department']
                        profile.phone = form.cleaned_data.get('phone', '')
                        profile.bio = form.cleaned_data.get('bio', '')
                        profile.is_verified = True
                        profile.created_by = request.user
                        profile.save()
                    
                    # Gửi email
                    if form.cleaned_data.get('send_welcome_email'):
                        send_welcome_email(user, password)
                    
                    messages.success(
                        request, 
                        f'Đã tạo tài khoản giảng viên thành công!\n'
                        f'Username: {username}\n'
                        f'Mật khẩu: {password}'
                    )
                    return redirect('core:admin_user_list')
                    
            except Exception as e:
                messages.error(request, f'Lỗi tạo tài khoản: {str(e)}')
    else:
        form = TeacherAccountForm()
    
    context = {
        'form': form,
        'title': 'Tạo tài khoản giảng viên',
    }
    
    return render(request, 'admin/create_account.html', context)


@login_required
@user_passes_test(is_admin)
def bulk_create_student_accounts(request):
    """Tạo hàng loạt tài khoản sinh viên từ file CSV"""
    if request.method == 'POST':
        form = BulkStudentAccountForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                password_option = form.cleaned_data.get('password_option')
                custom_password = form.cleaned_data.get('custom_password')
                send_welcome_email = form.cleaned_data.get('send_welcome_email')
                skip_errors = form.cleaned_data.get('skip_errors')
                
                # Xác định mật khẩu sẽ sử dụng
                if password_option == 'auto':
                    password = 'Student@123'
                    password_message = 'với mật khẩu mặc định: Student@123'
                else:
                    password = custom_password
                    password_message = 'với mật khẩu tùy chỉnh'
                
                # Đọc file CSV
                decoded_file = csv_file.read().decode('utf-8')
                csv_data = csv.DictReader(io.StringIO(decoded_file))
                
                success_count = 0
                error_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_data, 1):
                    try:
                        with transaction.atomic():
                            # Validate required fields
                            required_fields = ['student_id', 'email', 'first_name', 'last_name', 'department', 'year_of_study']
                            for field in required_fields:
                                if not row.get(field):
                                    raise ValueError(f'Thiếu trường bắt buộc: {field}')
                            
                            # Kiểm tra email đã tồn tại
                            email = row['email']
                            if User.objects.filter(email=email).exists():
                                raise ValueError(f'Email {email} đã được sử dụng')
                            
                            # Kiểm tra student_id đã tồn tại
                            student_id = row['student_id']
                            if UserProfile.objects.filter(student_id=student_id).exists():
                                raise ValueError(f'Mã sinh viên {student_id} đã tồn tại')
                            
                            # Tạo user
                            username = f"sv{student_id}"
                            
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=password,
                                first_name=row['first_name'],
                                last_name=row['last_name'],
                                is_active=True
                            )
                            
                            # Cập nhật profile
                            profile = user.profile
                            profile.role = 'student'
                            profile.student_id = student_id
                            profile.department = row['department']
                            profile.year_of_study = int(row['year_of_study'])
                            profile.phone = row.get('phone', '')
                            profile.is_verified = True
                            profile.created_by = request.user
                            profile.save()
                            
                            # Gửi email
                            if send_welcome_email:
                                send_welcome_email(user, password)
                            
                            success_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Dòng {row_num}: {str(e)}"
                        errors.append(error_msg)
                        
                        if not skip_errors:
                            raise e
                
                # Hiển thị kết quả
                if success_count > 0:
                    messages.success(request, f'Đã tạo thành công {success_count} tài khoản sinh viên {password_message}')
                
                if error_count > 0:
                    messages.warning(request, f'Có {error_count} lỗi xảy ra.')
                    for error in errors[:5]:  # Chỉ hiển thị 5 lỗi đầu
                        messages.error(request, error)
                
                return redirect('core:admin_user_list')
                
            except Exception as e:
                messages.error(request, f'Lỗi xử lý file CSV: {str(e)}')
    else:
        form = BulkStudentAccountForm()
    
    context = {
        'form': form,
        'title': 'Tạo hàng loạt tài khoản sinh viên',
    }
    
    return render(request, 'admin/bulk_create_accounts.html', context)


@login_required
@user_passes_test(is_admin)
def bulk_create_teacher_accounts(request):
    """Tạo hàng loạt tài khoản giảng viên từ file CSV"""
    if request.method == 'POST':
        form = BulkTeacherAccountForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                password_option = form.cleaned_data.get('password_option')
                custom_password = form.cleaned_data.get('custom_password')
                send_welcome_email = form.cleaned_data.get('send_welcome_email')
                skip_errors = form.cleaned_data.get('skip_errors')
                
                # Xác định mật khẩu sẽ sử dụng
                if password_option == 'auto':
                    password = 'Teacher@123'
                    password_message = 'với mật khẩu mặc định: Teacher@123'
                else:
                    password = custom_password
                    password_message = 'với mật khẩu tùy chỉnh'
                
                # Đọc file CSV
                decoded_file = csv_file.read().decode('utf-8')
                csv_data = csv.DictReader(io.StringIO(decoded_file))
                
                success_count = 0
                error_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_data, 1):
                    try:
                        with transaction.atomic():
                            # Validate required fields
                            required_fields = ['email', 'first_name', 'last_name', 'department']
                            for field in required_fields:
                                if not row.get(field):
                                    raise ValueError(f'Thiếu trường bắt buộc: {field}')
                            
                            # Kiểm tra email đã tồn tại
                            email = row['email']
                            if User.objects.filter(email=email).exists():
                                raise ValueError(f'Email {email} đã được sử dụng')
                            
                            # Tạo user
                            username = f"gv{get_random_string(6).lower()}"
                            
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=password,
                                first_name=row['first_name'],
                                last_name=row['last_name'],
                                is_active=True
                            )
                            
                            # Cập nhật profile
                            profile = user.profile
                            profile.role = 'teacher'
                            profile.department = row['department']
                            profile.phone = row.get('phone', '')
                            profile.bio = row.get('bio', '')
                            profile.is_verified = True
                            profile.created_by = request.user
                            profile.save()
                            
                            # Gửi email
                            if send_welcome_email:
                                send_welcome_email(user, password)
                            
                            success_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Dòng {row_num}: {str(e)}"
                        errors.append(error_msg)
                        
                        if not skip_errors:
                            raise e
                
                # Hiển thị kết quả
                if success_count > 0:
                    messages.success(request, f'Đã tạo thành công {success_count} tài khoản giảng viên {password_message}')
                
                if error_count > 0:
                    messages.warning(request, f'Có {error_count} lỗi xảy ra.')
                    for error in errors[:5]:  # Chỉ hiển thị 5 lỗi đầu
                        messages.error(request, error)
                
                return redirect('core:admin_user_list')
                
            except Exception as e:
                messages.error(request, f'Lỗi xử lý file CSV: {str(e)}')
    else:
        form = BulkTeacherAccountForm()
    
    context = {
        'form': form,
        'title': 'Tạo hàng loạt tài khoản giảng viên',
    }
    
    return render(request, 'admin/bulk_create_teacher_accounts.html', context)


@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    """Khóa/mở khóa tài khoản"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Không cho phép khóa chính mình
        if user == request.user:
            messages.error(request, 'Bạn không thể khóa tài khoản của chính mình.')
            return redirect('core:admin_user_list')
        
        # Không cho phép khóa superuser khác
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền khóa tài khoản superuser.')
            return redirect('core:admin_user_list')
        
        # Thay đổi trạng thái mà không trigger validation
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        
        status_text = "mở khóa" if user.is_active else "khóa"
        messages.success(request, f'Đã {status_text} tài khoản {user.username}.')
        
    except Exception as e:
        messages.error(request, f'Lỗi thay đổi trạng thái: {str(e)}')
    
    return redirect('core:admin_user_list')


@login_required
@user_passes_test(is_admin)
def reset_user_password(request, user_id):
    """Reset mật khẩu user"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Không cho phép reset mật khẩu của chính mình
        if user == request.user:
            messages.error(request, 'Bạn không thể reset mật khẩu của chính mình.')
            return redirect('core:admin_user_list')
        
        new_password = 'Student@123'  # Mật khẩu mặc định
        user.set_password(new_password)
        # Lưu password mà không trigger validation
        user.save(update_fields=['password'])
        
        messages.success(
            request, 
            f'Đã reset mật khẩu cho {user.username}.\n'
            f'Mật khẩu mới: {new_password}'
        )
        
    except Exception as e:
        messages.error(request, f'Lỗi reset mật khẩu: {str(e)}')
    
    return redirect('core:admin_user_list')


@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """Xóa tài khoản"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Không cho phép xóa chính mình
        if user == request.user:
            messages.error(request, 'Bạn không thể xóa tài khoản của chính mình.')
            return redirect('core:admin_user_list')
        
        # Không cho phép xóa superuser khác
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền xóa tài khoản superuser.')
            return redirect('core:admin_user_list')
        
        if request.method == 'POST':
            username = user.username
            user.delete()
            messages.success(request, f'Đã xóa tài khoản {username}.')
            return redirect('core:admin_user_list')
        
        context = {
            'user': user,
        }
        
        return render(request, 'admin/delete_user_confirm.html', context)
        
    except Exception as e:
        messages.error(request, f'Lỗi xóa tài khoản: {str(e)}')
        return redirect('core:admin_user_list')


def send_welcome_email(user, password):
    """Gửi email chào mừng"""
    try:
        subject = 'Chào mừng đến với Hệ thống Quản lý Học tập'
        message = f"""
        Xin chào {user.get_full_name()}!
        
        Tài khoản của bạn đã được tạo thành công.
        
        Thông tin đăng nhập:
        - Username: {user.username}
        - Email: {user.email}
        - Mật khẩu: {password}
        
        Vui lòng đăng nhập và đổi mật khẩu để bảo mật tài khoản.
        
        Trân trọng,
        Đội ngũ quản trị
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Lỗi gửi email: {str(e)}")


# API Views cho AJAX
@login_required
@user_passes_test(is_admin)
def user_search_api(request):
    """API tìm kiếm user cho Select2"""
    query = request.GET.get('q', '')
    role = request.GET.get('role', '')
    page = int(request.GET.get('page', 1))
    
    if not query or len(query) < 2:
        return JsonResponse({
            'results': [],
            'pagination': {'more': False}
        })
    
    # Base queryset
    users = User.objects.select_related('profile')
    
    # Filter by role if specified
    if role:
        users = users.filter(profile__role=role)
    
    # Search in name, username, email
    users = users.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query) |
        Q(email__icontains=query)
    ).order_by('first_name', 'last_name')
    
    # Pagination
    per_page = 20
    start = (page - 1) * per_page
    end = start + per_page
    
    # Format results for Select2
    results = []
    for user in users[start:end]:
        full_name = user.get_full_name() or user.username
        email = user.email or 'Không có email'
        department = getattr(user.profile, 'department', '') if hasattr(user, 'profile') and user.profile else ''
        
        if department:
            text = f"{full_name} ({email}) - {department}"
        else:
            text = f"{full_name} ({email})"
        
        results.append({
            'id': user.id,
            'text': text
        })
    
    # Check if there are more results
    has_more = users.count() > end
    
    return JsonResponse({
        'results': results,
        'pagination': {
            'more': has_more
        }
    })


def admin_search_classes(request):
    """API tìm kiếm lớp học cho admin"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if not query:
        return JsonResponse({
            'results': [],
            'pagination': {'more': False}
        })
    
    # Tìm kiếm lớp học
    from .models.study import Class
    classes = Class.objects.filter(
        Q(name__icontains=query) |
        Q(display_name__icontains=query) |
        Q(department__icontains=query) |
        Q(academic_year__icontains=query)
    ).filter(status='active').order_by('-academic_year', 'department', 'class_number')
    
    # Phân trang
    paginator = Paginator(classes, 10)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    results = []
    for class_obj in page_obj:
        results.append({
            'id': class_obj.id,
            'text': f"{class_obj.name} - {class_obj.display_name} ({class_obj.get_department_display()})"
        })
    
    return JsonResponse({
        'results': results,
        'pagination': {
            'more': page_obj.has_next()
        }
    })


@login_required
@user_passes_test(is_admin)
def admin_logout(request):
    """Admin logout - separate from user logout"""
    try:
        # Log the logout
        logger.info(f"Admin logout: {request.user.username}")
        
        # Only logout if this is an admin session
        if request.session.get('session_type') == 'admin':
            # Update login history
            from .models.authentication import LoginHistory
            latest_login = LoginHistory.objects.filter(
                user=request.user,
                success=True,
                logout_time__isnull=True
            ).order_by('-login_time').first()
            
            if latest_login:
                latest_login.logout_time = timezone.now()
                latest_login.save()
            
            # Logout admin session
            logout(request)
            
            messages.success(request, 'Đăng xuất admin thành công!')
            
            # Create response with cookie deletion
            response = redirect('core:admin_login')
            response.delete_cookie('admin_sessionid', path='/admin/')
            response.delete_cookie('sessionid', path='/')
            
            return response
        else:
            messages.warning(request, 'Bạn không có phiên admin để đăng xuất.')
            return redirect('core:admin_login')
            
    except Exception as e:
        logger.error(f"Admin logout error: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi đăng xuất.')
        return redirect('core:admin_login') 