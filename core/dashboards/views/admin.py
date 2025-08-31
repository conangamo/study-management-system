"""
Admin Dashboard Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Avg, Count, Sum, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import csv
import io

from .base import BaseDashboardView, AjaxResponseMixin, StatisticsMixin
from core.models import (
    Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, 
    Note, Tag, UserProfile, UserRole, LoginHistory, StudentAccountRequest
)
from core.forms import UserCreationForm, UserUpdateForm, CourseForm


class AdminDashboardView(BaseDashboardView, StatisticsMixin):
    """Trang chủ dashboard cho admin"""
    template_name = 'dashboards/admin/dashboard.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or self.get_user_role() == 'admin'))
    
    def get_dashboard_type(self):
        return 'admin'
    
    def get_page_title(self):
        return 'Dashboard Quản Trị'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê tổng quan hệ thống
        context.update({
            'system_stats': self.get_system_statistics(),
            'user_stats': self.get_user_statistics(),
            'academic_stats': self.get_academic_statistics(),
            'activity_stats': self.get_activity_statistics(),
        })
        
        # Dữ liệu hoạt động gần đây
        context.update({
            'recent_users': self.get_recent_users(),
            'recent_courses': self.get_recent_courses(),
            'recent_activities': self.get_recent_activities(),
            'pending_requests': self.get_pending_requests(),
            'system_alerts': self.get_system_alerts(),
        })
        
        return context
    
    def get_system_statistics(self):
        """Thống kê tổng quan hệ thống"""
        total_users = User.objects.count()
        total_courses = Course.objects.count()
        total_assignments = Assignment.objects.count()
        total_grades = Grade.objects.count()
        
        # Thống kê theo thời gian
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
        new_courses_week = Course.objects.filter(created_at__gte=week_ago).count()
        
        return {
            'total_users': total_users,
            'total_courses': total_courses,
            'total_assignments': total_assignments,
            'total_grades': total_grades,
            'new_users_week': new_users_week,
            'new_courses_week': new_courses_week,
        }
    
    def get_user_statistics(self):
        """Thống kê người dùng"""
        students_count = User.objects.filter(
            profile__role__name='student'
        ).count()
        
        teachers_count = User.objects.filter(
            profile__role__name='teacher'
        ).count()
        
        admins_count = User.objects.filter(
            Q(is_superuser=True) | Q(profile__role__name='admin')
        ).count()
        
        active_users = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return {
            'students_count': students_count,
            'teachers_count': teachers_count,
            'admins_count': admins_count,
            'active_users': active_users,
        }
    
    def get_academic_statistics(self):
        """Thống kê học tập"""
        active_courses = Course.objects.filter(status='active').count()
        total_enrollments = CourseEnrollment.objects.filter(
            status='enrolled'
        ).count()
        
        pending_assignments = Assignment.objects.filter(
            status='submission_open'
        ).count()
        
        average_grade = Grade.objects.aggregate(
            avg=Avg('score')
        )['avg']
        
        return {
            'active_courses': active_courses,
            'total_enrollments': total_enrollments,
            'pending_assignments': pending_assignments,
            'average_grade': round(average_grade, 2) if average_grade else 0,
        }
    
    def get_activity_statistics(self):
        """Thống kê hoạt động"""
        today = timezone.now().date()
        
        logins_today = LoginHistory.objects.filter(
            login_time__date=today,
            success=True
        ).count()
        
        submissions_today = AssignmentSubmission.objects.filter(
            submitted_at__date=today
        ).count()
        
        grades_today = Grade.objects.filter(
            created_at__date=today
        ).count()
        
        return {
            'logins_today': logins_today,
            'submissions_today': submissions_today,
            'grades_today': grades_today,
        }
    
    def get_recent_users(self):
        """Lấy người dùng mới nhất"""
        return User.objects.select_related('profile').order_by('-date_joined')[:5]
    
    def get_recent_courses(self):
        """Lấy môn học mới nhất"""
        return Course.objects.select_related('teacher').order_by('-created_at')[:5]
    
    def get_recent_activities(self):
        """Lấy hoạt động gần đây"""
        return LoginHistory.objects.select_related('user').order_by('-login_time')[:10]
    
    def get_pending_requests(self):
        """Lấy yêu cầu đang chờ xử lý"""
        return StudentAccountRequest.objects.filter(
            status='pending'
        ).order_by('-created_at')[:5]
    
    def get_system_alerts(self):
        """Lấy cảnh báo hệ thống"""
        alerts = []
        
        # Kiểm tra courses sắp kết thúc
        ending_soon = Course.objects.filter(
            status='active',
            end_date__lte=timezone.now().date() + timedelta(days=7)
        ).count()
        
        if ending_soon > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{ending_soon} môn học sắp kết thúc trong 7 ngày tới'
            })
        
        # Kiểm tra assignments quá hạn
        overdue_assignments = Assignment.objects.filter(
            status='submission_open',
            due_date__lt=timezone.now()
        ).count()
        
        if overdue_assignments > 0:
            alerts.append({
                'type': 'danger',
                'message': f'{overdue_assignments} bài tập đã quá hạn nộp'
            })
        
        return alerts


class AdminUserView(BaseDashboardView, AjaxResponseMixin):
    """Quản lý người dùng"""
    template_name = 'dashboards/admin/users.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or self.get_user_role() == 'admin'))
    
    def get_page_title(self):
        return 'Quản Lý Người Dùng'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/admin/'},
            {'title': 'Người Dùng', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy danh sách users
        users = User.objects.select_related('profile').order_by('-date_joined')
        
        # Filter theo role
        role_filter = self.request.GET.get('role')
        if role_filter:
            if role_filter == 'admin':
                users = users.filter(
                    Q(is_superuser=True) | Q(profile__role__name='admin')
                )
            else:
                users = users.filter(profile__role__name=role_filter)
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(users, 20)
        page = self.request.GET.get('page')
        users_page = paginator.get_page(page)
        
        # Thống kê
        user_stats = {
            'total': User.objects.count(),
            'students': User.objects.filter(profile__role__name='student').count(),
            'teachers': User.objects.filter(profile__role__name='teacher').count(),
            'admins': User.objects.filter(
                Q(is_superuser=True) | Q(profile__role__name='admin')
            ).count(),
            'active': User.objects.filter(is_active=True).count(),
        }
        
        # Lấy roles cho filter
        roles = UserRole.objects.all()
        
        context.update({
            'users': users_page,
            'user_stats': user_stats,
            'roles': roles,
            'selected_role': role_filter,
            'search_query': search_query,
            'user_form': UserCreationForm(),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Tạo user mới"""
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            if self.is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Người dùng đã được tạo thành công!',
                    'user_id': user.id
                })
            else:
                messages.success(request, 'Người dùng đã được tạo thành công!')
                return redirect('core:admin_users')
        
        if self.is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        return self.get(request, *args, **kwargs)


class AdminUserDetailView(BaseDashboardView):
    """Chi tiết người dùng"""
    template_name = 'dashboards/admin/user_detail.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or self.get_user_role() == 'admin'))
    
    def get_page_title(self):
        user = self.get_user()
        return f'Người dùng: {user.get_full_name()}' if user else 'Chi tiết người dùng'
    
    def get_breadcrumb(self):
        user = self.get_user()
        return [
            {'title': 'Dashboard', 'url': '/dashboard/admin/'},
            {'title': 'Người Dùng', 'url': '/dashboard/admin/users/'},
            {'title': user.get_full_name() if user else 'Chi tiết', 'url': '#'}
        ]
    
    def get_user(self):
        """Lấy user object"""
        if not hasattr(self, '_user'):
            user_id = self.kwargs.get('user_id')
            self._user = get_object_or_404(User, id=user_id)
        return self._user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_user()
        
        # Lấy thông tin chi tiết
        profile = getattr(user, 'profile', None)
        
        # Lấy hoạt động
        login_history = LoginHistory.objects.filter(
            user=user
        ).order_by('-login_time')[:10]
        
        # Thống kê theo role
        user_stats = {}
        
        if profile and profile.role.name == 'student':
            enrollments = CourseEnrollment.objects.filter(student=user)
            grades = Grade.objects.filter(student=user)
            
            user_stats = {
                'total_courses': enrollments.count(),
                'active_courses': enrollments.filter(
                    status='enrolled',
                    course__status='active'
                ).count(),
                'completed_courses': enrollments.filter(status='completed').count(),
                'average_grade': grades.aggregate(avg=Avg('score'))['avg'] or 0,
                'total_grades': grades.count(),
            }
            
        elif profile and profile.role.name == 'teacher':
            courses = Course.objects.filter(teacher=user)
            assignments = Assignment.objects.filter(course__teacher=user)
            
            user_stats = {
                'total_courses': courses.count(),
                'active_courses': courses.filter(status='active').count(),
                'total_assignments': assignments.count(),
                'total_students': CourseEnrollment.objects.filter(
                    course__in=courses,
                    status='enrolled'
                ).count(),
            }
        
        context.update({
            'user_detail': user,
            'profile': profile,
            'login_history': login_history,
            'user_stats': user_stats,
        })
        
        return context


class AdminSystemView(BaseDashboardView):
    """Quản lý hệ thống"""
    template_name = 'dashboards/admin/system.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or self.get_user_role() == 'admin'))
    
    def get_page_title(self):
        return 'Quản Lý Hệ Thống'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/admin/'},
            {'title': 'Hệ Thống', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê database
        db_stats = {
            'users': User.objects.count(),
            'courses': Course.objects.count(),
            'enrollments': CourseEnrollment.objects.count(),
            'assignments': Assignment.objects.count(),
            'submissions': AssignmentSubmission.objects.count(),
            'grades': Grade.objects.count(),
            'notes': Note.objects.count(),
            'login_history': LoginHistory.objects.count(),
        }
        
        # Thống kê storage (giả lập)
        storage_stats = {
            'total_files': AssignmentSubmission.objects.exclude(
                file_submission__isnull=True
            ).count(),
            'total_size': '2.5 GB',  # Tính toán thực tế nếu cần
        }
        
        # System health
        system_health = {
            'database': 'healthy',
            'storage': 'healthy',
            'cache': 'healthy',
            'last_backup': '2 hours ago',  # Thực tế lấy từ log
        }
        
        # Recent errors (giả lập)
        recent_errors = []
        
        context.update({
            'db_stats': db_stats,
            'storage_stats': storage_stats,
            'system_health': system_health,
            'recent_errors': recent_errors,
        })
        
        return context


class AdminAnalyticsView(BaseDashboardView):
    """Phân tích và báo cáo"""
    template_name = 'dashboards/admin/analytics.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or self.get_user_role() == 'admin'))
    
    def get_page_title(self):
        return 'Phân Tích & Báo Cáo'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/admin/'},
            {'title': 'Phân Tích', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê đăng ký theo thời gian
        registration_stats = self.get_registration_analytics()
        
        # Thống kê điểm số
        grade_analytics = self.get_grade_analytics()
        
        # Thống kê hoạt động
        activity_analytics = self.get_activity_analytics()
        
        # Thống kê môn học phổ biến
        popular_courses = self.get_popular_courses()
        
        context.update({
            'registration_stats': registration_stats,
            'grade_analytics': grade_analytics,
            'activity_analytics': activity_analytics,
            'popular_courses': popular_courses,
        })
        
        return context
    
    def get_registration_analytics(self):
        """Phân tích đăng ký theo thời gian"""
        # Lấy data 12 tháng gần nhất
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        monthly_registrations = {}
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_key = current_date.strftime('%Y-%m')
            
            registrations = User.objects.filter(
                date_joined__gte=current_date,
                date_joined__lt=next_month
            ).count()
            
            monthly_registrations[month_key] = registrations
            current_date = next_month
        
        return {
            'labels': list(monthly_registrations.keys()),
            'values': list(monthly_registrations.values()),
        }
    
    def get_grade_analytics(self):
        """Phân tích điểm số"""
        grades = Grade.objects.all()
        
        if not grades.exists():
            return {}
        
        # Phân bố điểm
        grade_distribution = {}
        for grade in grades:
            score_range = f"{int(grade.score//1)}-{int(grade.score//1)+1}"
            grade_distribution[score_range] = grade_distribution.get(score_range, 0) + 1
        
        # Điểm trung bình theo môn
        courses_avg = {}
        for course in Course.objects.all():
            course_grades = grades.filter(course=course)
            if course_grades.exists():
                avg = course_grades.aggregate(avg=Avg('score'))['avg']
                courses_avg[course.name] = round(avg, 2)
        
        return {
            'distribution': grade_distribution,
            'courses_average': courses_avg,
            'overall_average': round(grades.aggregate(avg=Avg('score'))['avg'], 2),
        }
    
    def get_activity_analytics(self):
        """Phân tích hoạt động"""
        # Hoạt động đăng nhập 7 ngày gần nhất
        daily_logins = {}
        
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            logins = LoginHistory.objects.filter(
                login_time__date=date,
                success=True
            ).count()
            daily_logins[date.strftime('%Y-%m-%d')] = logins
        
        return {
            'daily_logins': daily_logins,
        }
    
    def get_popular_courses(self):
        """Lấy môn học phổ biến"""
        return Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:10]


class AdminImportView(BaseDashboardView, AjaxResponseMixin):
    """Import dữ liệu từ CSV"""
    template_name = 'dashboards/admin/import.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                (self.request.user.is_superuser or self.get_user_role() == 'admin'))
    
    def get_page_title(self):
        return 'Import Dữ Liệu'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/admin/'},
            {'title': 'Import', 'url': '#'}
        ]
    
    def post(self, request, *args, **kwargs):
        """Xử lý import CSV"""
        if 'csv_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng chọn file CSV'
            }, status=400)
        
        csv_file = request.FILES['csv_file']
        import_type = request.POST.get('import_type')
        
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({
                'success': False,
                'message': 'File phải có định dạng CSV'
            }, status=400)
        
        try:
            # Đọc file CSV
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(file_data))
            
            success_count = 0
            error_count = 0
            errors = []
            
            if import_type == 'users':
                success_count, error_count, errors = self.import_users(csv_data)
            elif import_type == 'courses':
                success_count, error_count, errors = self.import_courses(csv_data)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Loại import không hợp lệ'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'Import thành công {success_count} bản ghi. Lỗi: {error_count}',
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors[:10]  # Chỉ trả về 10 lỗi đầu tiên
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Lỗi khi xử lý file: {str(e)}'
            }, status=500)
    
    def import_users(self, csv_data):
        """Import users từ CSV"""
        success_count = 0
        error_count = 0
        errors = []
        
        for row in csv_data:
            try:
                # Tạo user mới
                user = User.objects.create_user(
                    username=row.get('username'),
                    email=row.get('email'),
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    password=row.get('password', 'default123')
                )
                
                # Tạo profile nếu có role
                role_name = row.get('role')
                if role_name:
                    try:
                        role = UserRole.objects.get(name=role_name)
                        UserProfile.objects.create(
                            user=user,
                            role=role,
                            student_id=row.get('student_id', ''),
                            phone_number=row.get('phone_number', ''),
                            date_of_birth=row.get('date_of_birth') or None,
                        )
                    except UserRole.DoesNotExist:
                        errors.append(f'Role {role_name} không tồn tại cho user {user.username}')
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f'Lỗi tạo user {row.get("username", "unknown")}: {str(e)}')
        
        return success_count, error_count, errors
    
    def import_courses(self, csv_data):
        """Import courses từ CSV"""
        success_count = 0
        error_count = 0
        errors = []
        
        for row in csv_data:
            try:
                # Tìm teacher
                teacher_username = row.get('teacher_username')
                try:
                    teacher = User.objects.get(username=teacher_username)
                except User.DoesNotExist:
                    error_count += 1
                    errors.append(f'Teacher {teacher_username} không tồn tại')
                    continue
                
                # Tạo course
                course = Course.objects.create(
                    name=row.get('name'),
                    code=row.get('code'),
                    description=row.get('description', ''),
                    credits=int(row.get('credits', 3)),
                    semester=row.get('semester', '1'),
                    academic_year=row.get('academic_year'),
                    start_date=row.get('start_date'),
                    end_date=row.get('end_date'),
                    teacher=teacher,
                    max_students=int(row.get('max_students', 50)),
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f'Lỗi tạo course {row.get("code", "unknown")}: {str(e)}')
        
        return success_count, error_count, errors 