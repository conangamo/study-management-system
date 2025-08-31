"""
Admin Dashboard Views
- User Management: Manage accounts, import CSV
- System Management: Manage all data 
- Analytics: Reports, activity logs
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView, View
)
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime, timedelta
import json
import csv
import io
import logging
logger = logging.getLogger('core')

from core.models.study import Course, Grade
from core.models.assignment import Assignment, AssignmentSubmission
from core.models.user import UserProfile
from core.models.academic import (
    AcademicYear, Department
)
from core.models.authentication import LoginHistory
from .forms import (
    AdminUserCreateForm, AdminUserUpdateForm, AdminUserImportForm,
    AdminBulkUserActionForm, AdminResetPasswordForm, AdminSystemSettingsForm,
    AdminCourseForm
)
from .mixins import AdminRequiredMixin
from .utils import generate_user_report, backup_database


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin Dashboard main view"""
    template_name = 'dashboards/admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        students = User.objects.filter(profile__role='student').count()
        teachers = User.objects.filter(profile__role='teacher').count()
        admins = User.objects.filter(profile__role='admin').count()
        
        # System statistics
        total_courses = Course.objects.count()
        active_courses = Course.objects.filter(status='active').count()
        total_assignments = Assignment.objects.count()
        total_grades = Grade.objects.count()
        
        # Recent activity
        recent_logins = LoginHistory.objects.order_by('-login_time')[:10]
        recent_users = User.objects.order_by('-date_joined')[:5]
        
        context.update({
            # User stats
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'students_count': students,
            'teachers_count': teachers,
            'admins_count': admins,
            
            # System stats
            'total_courses': total_courses,
            'active_courses': active_courses,
            'total_assignments': total_assignments,
            'total_grades': total_grades,
            
            # Recent activity
            'recent_logins': recent_logins,
            'recent_users': recent_users,
            
            # Quick stats for charts
            'user_growth_data': self.get_user_growth_data(),
            'course_status_data': self.get_course_status_data(),
        })
        
        return context
    
    def get_user_growth_data(self):
        """Get user growth data for last 30 days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        data = []
        current_date = start_date
        while current_date <= end_date:
            count = User.objects.filter(date_joined__date=current_date).count()
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': count
            })
            current_date += timedelta(days=1)
        
        return data
    
    def get_course_status_data(self):
        """Get course status distribution"""
        status_counts = Course.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return list(status_counts)


# =============================================================================
# USER MANAGEMENT VIEWS
# =============================================================================

class AdminUserListView(AdminRequiredMixin, ListView):
    """List all users with filtering and search"""
    model = User
    template_name = 'dashboards/admin/user/list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.select_related('profile').order_by('-date_joined')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(profile__student_id__icontains=search)
            )
        
        # Role filter
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(profile__role=role)
        
        # Status filter
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Department filter
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(profile__department=department)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filter options
        context.update({
            'role_choices': UserProfile.ROLE_CHOICES,
            'department_choices': UserProfile.DEPARTMENT_CHOICES,
            'search_query': self.request.GET.get('search', ''),
            'selected_role': self.request.GET.get('role', ''),
            'selected_status': self.request.GET.get('status', ''),
            'selected_department': self.request.GET.get('department', ''),
        })
        
        # Statistics
        total_count = self.get_queryset().count()
        context['total_users'] = total_count
        
        return context


class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """User detail view for admin"""
    model = User
    template_name = 'dashboards/admin/user/detail.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # User activity
        context['login_history'] = LoginHistory.objects.filter(
            user=user
        ).order_by('-login_time')[:10]
        
        # Academic data for students
        if hasattr(user, 'profile') and user.profile.is_student:
            context['enrolled_courses'] = Course.objects.filter(students=user)
            context['grades'] = Grade.objects.filter(student=user).order_by('-date')[:10]
            context['submissions'] = AssignmentSubmission.objects.filter(
                student=user
            ).order_by('-submitted_at')[:10]
        
        # Teaching data for teachers
        if hasattr(user, 'profile') and user.profile.is_teacher:
            context['teaching_courses'] = Course.objects.filter(teacher=user)
            context['created_assignments'] = Assignment.objects.filter(
                created_by=user
            ).order_by('-created_at')[:10]
        
        return context


class AdminUserCreateView(AdminRequiredMixin, CreateView):
    """Create new user"""
    model = User
    form_class = AdminUserCreateForm
    template_name = 'dashboards/admin/user/create.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Người dùng đã được tạo thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:admin:user_detail', kwargs={'pk': self.object.pk})


class AdminUserUpdateView(AdminRequiredMixin, UpdateView):
    """Update user"""
    model = User
    form_class = AdminUserUpdateForm
    template_name = 'dashboards/admin/user/edit.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Thông tin người dùng đã được cập nhật!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:admin:user_detail', kwargs={'pk': self.object.pk})


class AdminUserDeleteView(AdminRequiredMixin, DeleteView):
    """Delete user"""
    model = User
    template_name = 'dashboards/admin/user/delete.html'
    success_url = reverse_lazy('dashboards:admin:user_list')
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, 'Bạn không thể xóa tài khoản của chính mình!')
            return redirect('dashboards:admin:user_detail', pk=user.pk)
        
        messages.success(request, f'Đã xóa người dùng {user.get_full_name()}!')
        return super().delete(request, *args, **kwargs)


class AdminToggleUserStatusView(AdminRequiredMixin, View):
    """Toggle user active status"""
    
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        if user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'Bạn không thể thay đổi trạng thái của chính mình!'
            })
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'kích hoạt' if user.is_active else 'vô hiệu hóa'
        
        return JsonResponse({
            'success': True,
            'message': f'Đã {status} tài khoản {user.get_full_name()}!',
            'new_status': user.is_active
        })


class AdminResetPasswordView(AdminRequiredMixin, FormView):
    """Reset user password"""
    form_class = AdminResetPasswordForm
    template_name = 'dashboards/admin/user/reset_password.html'
    
    def get_user(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.get_user()
        return context
    
    def form_valid(self, form):
        user = self.get_user()
        new_password = form.cleaned_data['new_password']
        user.set_password(new_password)
        user.save()
        
        messages.success(
            self.request, 
            f'Đã đặt lại mật khẩu cho {user.get_full_name()}!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:admin:user_detail', kwargs={'pk': self.kwargs['pk']})


class AdminUserImportView(AdminRequiredMixin, FormView):
    """Import users from CSV"""
    form_class = AdminUserImportForm
    template_name = 'dashboards/admin/user/import.html'
    success_url = reverse_lazy('dashboards:admin:user_list')
    
    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(decoded_file))
            
            created_users = []
            errors = []
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_data, start=2):
                    try:
                        # Create user
                        user = User.objects.create_user(
                            username=row['username'],
                            email=row['email'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            password=row.get('password', 'defaultpassword123')
                        )
                        
                        # Create profile
                        profile = UserProfile.objects.create(
                            user=user,
                            role=row['role'],
                            student_id=row.get('student_id', ''),
                            department=row.get('department', ''),
                            phone=row.get('phone', ''),
                            created_by=self.request.user
                        )
                        
                        created_users.append(user)
                        
                    except Exception as e:
                        errors.append(f'Dòng {row_num}: {str(e)}')
            
            if created_users:
                messages.success(
                    self.request,
                    f'Đã tạo thành công {len(created_users)} người dùng!'
                )
            
            if errors:
                error_msg = 'Có lỗi khi tạo một số người dùng:\n' + '\n'.join(errors)
                messages.warning(self.request, error_msg)
                
        except Exception as e:
            messages.error(self.request, f'Lỗi khi đọc file CSV: {str(e)}')
            return self.form_invalid(form)
        
        return super().form_valid(form)


class AdminUserExportView(AdminRequiredMixin, View):
    """Export users to CSV"""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Username', 'Email', 'First Name', 'Last Name',
            'Role', 'Student ID', 'Department', 'Phone', 'Is Active',
            'Date Joined', 'Last Login'
        ])
        
        users = User.objects.select_related('profile').all()
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.profile.role if hasattr(user, 'profile') else '',
                user.profile.student_id if hasattr(user, 'profile') else '',
                user.profile.department if hasattr(user, 'profile') else '',
                user.profile.phone if hasattr(user, 'profile') else '',
                user.is_active,
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
            ])
        
        return response


class AdminBulkUserActionsView(AdminRequiredMixin, FormView):
    """Bulk actions on users"""
    form_class = AdminBulkUserActionForm
    template_name = 'dashboards/admin/user/bulk_actions.html'
    success_url = reverse_lazy('dashboards:admin:user_list')
    
    def form_valid(self, form):
        action = form.cleaned_data['action']
        user_ids = form.cleaned_data['user_ids']
        users = User.objects.filter(id__in=user_ids)
        
        if self.request.user.id in user_ids:
            messages.error(self.request, 'Bạn không thể thực hiện hành động trên chính mình!')
            return self.form_invalid(form)
        
        count = 0
        try:
            with transaction.atomic():
                if action == 'activate':
                    users.update(is_active=True)
                    count = users.count()
                    messages.success(self.request, f'Đã kích hoạt {count} người dùng!')
                    
                elif action == 'deactivate':
                    users.update(is_active=False)
                    count = users.count()
                    messages.success(self.request, f'Đã vô hiệu hóa {count} người dùng!')
                    
                elif action == 'delete':
                    count = users.count()
                    users.delete()
                    messages.success(self.request, f'Đã xóa {count} người dùng!')
                    
        except Exception as e:
            messages.error(self.request, f'Lỗi khi thực hiện hành động: {str(e)}')
            return self.form_invalid(form)
        
        return super().form_valid(form)


# =============================================================================
# SYSTEM MANAGEMENT VIEWS
# =============================================================================

class AdminSystemManagementView(AdminRequiredMixin, TemplateView):
    """System management overview"""
    template_name = 'dashboards/admin/system/management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System statistics
        context.update({
            'total_courses': Course.objects.count(),
            'total_assignments': Assignment.objects.count(),
            'total_grades': Grade.objects.count(),
            'total_submissions': AssignmentSubmission.objects.count(),
            'disk_usage': self.get_disk_usage(),
            'database_size': self.get_database_size(),
        })
        
        return context
    
    def get_disk_usage(self):
        """Get disk usage information"""
        import shutil
        total, used, free = shutil.disk_usage('/')
        return {
            'total': total // (1024**3),  # GB
            'used': used // (1024**3),    # GB
            'free': free // (1024**3),    # GB
            'percent': (used / total) * 100
        }
    
    def get_database_size(self):
        """Get database size (simplified)"""
        # This would need to be implemented based on your database
        return "N/A"


class AdminCourseListView(AdminRequiredMixin, ListView):
    """Danh sách môn học với tìm kiếm/lọc"""
    model = Course
    template_name = 'dashboards/admin/system/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        qs = Course.objects.select_related('teacher', 'academic_year').prefetch_related('assistant_teachers', 'students')
        q = self.request.GET.get('q')
        teacher = self.request.GET.get('teacher')
        year = self.request.GET.get('year')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))
        if teacher:
            qs = qs.filter(Q(teacher_id=teacher) | Q(assistant_teachers__id=teacher))
        if year:
            qs = qs.filter(academic_year_id=year)
        return qs.distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'teachers': User.objects.filter(profile__role='teacher').order_by('last_name', 'first_name'),
            'years': AcademicYear.objects.all().order_by('-start_date'),
            'q': self.request.GET.get('q', ''),
            'filter_teacher': self.request.GET.get('teacher', ''),
            'filter_year': self.request.GET.get('year', ''),
        })
        return context


class AdminCourseCreateView(AdminRequiredMixin, CreateView):
    """Tạo môn học mới"""
    model = Course
    form_class = AdminCourseForm
    template_name = 'dashboards/admin/system/course_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        assistants = form.cleaned_data.get('assistant_teachers')
        if assistants is not None:
            self.object.assistant_teachers.set(assistants)
        messages.success(self.request, 'Đã tạo môn học thành công.')
        logger.info('COURSE_CREATE user=%s course_id=%s code=%s name=%s', self.request.user.id, self.object.id, self.object.code, self.object.name)
        return response

    def get_success_url(self):
        return reverse('dashboards:admin:courses:list')


class AdminCourseUpdateView(AdminRequiredMixin, UpdateView):
    """Sửa môn học"""
    model = Course
    form_class = AdminCourseForm
    template_name = 'dashboards/admin/system/course_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        assistants = form.cleaned_data.get('assistant_teachers')
        if assistants is not None:
            self.object.assistant_teachers.set(assistants)
        messages.success(self.request, 'Đã cập nhật môn học.')
        logger.info('COURSE_UPDATE user=%s course_id=%s code=%s name=%s', self.request.user.id, self.object.id, self.object.code, self.object.name)
        return response

    def get_success_url(self):
        return reverse('dashboards:admin:courses:list')


class AdminCourseDeleteView(AdminRequiredMixin, DeleteView):
    """Xóa môn học"""
    model = Course
    template_name = 'dashboards/admin/system/course_confirm_delete.html'
    success_url = reverse_lazy('dashboards:admin:courses:list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        logger.info('COURSE_DELETE user=%s course_id=%s code=%s name=%s', request.user.id, obj.id, obj.code, obj.name)
        messages.success(request, 'Đã xóa môn học.')
        return super().delete(request, *args, **kwargs)


class AdminAssignmentManagementView(AdminRequiredMixin, ListView):
    """Manage all assignments"""
    model = Assignment
    template_name = 'dashboards/admin/system/assignments.html'
    context_object_name = 'assignments'
    paginate_by = 20
    
    def get_queryset(self):
        return Assignment.objects.select_related('course', 'created_by').order_by('-created_at')


class AdminGradeManagementView(AdminRequiredMixin, ListView):
    """Manage all grades"""
    model = Grade
    template_name = 'dashboards/admin/system/grades.html'
    context_object_name = 'grades'
    paginate_by = 20
    
    def get_queryset(self):
        return Grade.objects.select_related('student', 'course', 'created_by').order_by('-created_at')


class AdminDatabaseManagementView(AdminRequiredMixin, TemplateView):
    """Database management tools"""
    template_name = 'dashboards/admin/system/database.html'


class AdminBackupView(AdminRequiredMixin, View):
    """Create database backup"""
    
    def post(self, request):
        try:
            backup_file = backup_database()
            messages.success(request, f'Backup đã được tạo: {backup_file}')
        except Exception as e:
            messages.error(request, f'Lỗi khi tạo backup: {str(e)}')
        
        return redirect('dashboards:admin:database_management')


class AdminLogsView(AdminRequiredMixin, TemplateView):
    """View system logs"""
    template_name = 'dashboards/admin/system/logs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recent login history
        context['recent_logins'] = LoginHistory.objects.order_by('-login_time')[:50]
        
        return context


# =============================================================================
# ANALYTICS VIEWS
# =============================================================================

class AdminAnalyticsView(AdminRequiredMixin, TemplateView):
    """Analytics overview"""
    template_name = 'dashboards/admin/analytics/overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # User analytics
        context['user_stats'] = self.get_user_statistics()
        context['course_stats'] = self.get_course_statistics()
        context['grade_stats'] = self.get_grade_statistics()
        context['activity_stats'] = self.get_activity_statistics()
        
        return context
    
    def get_user_statistics(self):
        """Get user statistics"""
        return {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'students': User.objects.filter(profile__role='student').count(),
            'teachers': User.objects.filter(profile__role='teacher').count(),
            'admins': User.objects.filter(profile__role='admin').count(),
        }
    
    def get_course_statistics(self):
        """Get course statistics"""
        return {
            'total': Course.objects.count(),
            'active': Course.objects.filter(status='active').count(),
            'upcoming': Course.objects.filter(status='upcoming').count(),
            'completed': Course.objects.filter(status='completed').count(),
        }
    
    def get_grade_statistics(self):
        """Get grade statistics"""
        grades = Grade.objects.all()
        if grades.exists():
            return {
                'total': grades.count(),
                'average': grades.aggregate(avg=Avg('score'))['avg'],
                'highest': grades.aggregate(max=Max('score'))['max'],
                'lowest': grades.aggregate(min=Min('score'))['min'],
            }
        return {'total': 0, 'average': 0, 'highest': 0, 'lowest': 0}
    
    def get_activity_statistics(self):
        """Get activity statistics"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        return {
            'logins_today': LoginHistory.objects.filter(login_time__date=today).count(),
            'logins_week': LoginHistory.objects.filter(login_time__date__gte=week_ago).count(),
            'new_users_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
        }


class AdminUserAnalyticsView(AdminRequiredMixin, TemplateView):
    """User analytics"""
    template_name = 'dashboards/admin/analytics/users.html'


class AdminCourseAnalyticsView(AdminRequiredMixin, TemplateView):
    """Course analytics"""
    template_name = 'dashboards/admin/analytics/courses.html'


class AdminGradeAnalyticsView(AdminRequiredMixin, TemplateView):
    """Grade analytics"""
    template_name = 'dashboards/admin/analytics/grades.html'


class AdminActivityLogView(AdminRequiredMixin, ListView):
    """Activity log view"""
    model = LoginHistory
    template_name = 'dashboards/admin/analytics/activity.html'
    context_object_name = 'activities'
    paginate_by = 50
    
    def get_queryset(self):
        return LoginHistory.objects.select_related('user').order_by('-login_time')


class AdminReportsView(AdminRequiredMixin, TemplateView):
    """Reports dashboard"""
    template_name = 'dashboards/admin/analytics/reports.html'


class AdminExportReportView(AdminRequiredMixin, View):
    """Export system report"""
    
    def get(self, request):
        report_type = request.GET.get('type', 'full')
        format_type = request.GET.get('format', 'csv')
        
        if format_type == 'csv':
            return self.export_csv_report(report_type)
        else:
            return self.export_json_report(report_type)
    
    def export_csv_report(self, report_type):
        """Export CSV report"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="report_{report_type}.csv"'
        
        # Implementation depends on report_type
        # This is a simplified version
        writer = csv.writer(response)
        writer.writerow(['Report Type', 'Generated At', 'Total Users', 'Total Courses'])
        writer.writerow([
            report_type,
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            User.objects.count(),
            Course.objects.count()
        ])
        
        return response
    
    def export_json_report(self, report_type):
        """Export JSON report"""
        data = {
            'report_type': report_type,
            'generated_at': timezone.now().isoformat(),
            'summary': {
                'total_users': User.objects.count(),
                'total_courses': Course.objects.count(),
                'total_assignments': Assignment.objects.count(),
                'total_grades': Grade.objects.count(),
            }
        }
        
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="report_{report_type}.json"'
        
        return response


# =============================================================================
# API VIEWS
# =============================================================================

class AdminUserSearchAPIView(AdminRequiredMixin, View):
    """User search API for AJAX"""
    
    def get(self, request):
        search = request.GET.get('q', '')
        
        users = User.objects.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        ).select_related('profile')[:10]
        
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'email': user.email,
                'role': user.profile.role if hasattr(user, 'profile') else '',
                'is_active': user.is_active,
            })
        
        return JsonResponse({'users': data})


class AdminStatsAPIView(AdminRequiredMixin, View):
    """Statistics API for dashboard charts"""
    
    def get(self, request):
        stats_type = request.GET.get('type', 'overview')
        
        if stats_type == 'user_growth':
            return JsonResponse({'data': self.get_user_growth_data()})
        elif stats_type == 'course_status':
            return JsonResponse({'data': self.get_course_status_data()})
        elif stats_type == 'grade_distribution':
            return JsonResponse({'data': self.get_grade_distribution_data()})
        else:
            return JsonResponse({'data': []})
    
    def get_user_growth_data(self):
        """User growth over last 30 days"""
        # Implementation similar to dashboard view
        return []
    
    def get_course_status_data(self):
        """Course status distribution"""
        # Implementation similar to dashboard view
        return []
    
    def get_grade_distribution_data(self):
        """Grade distribution"""
        # Implementation for grade distribution
        return []


class AdminActivityDataAPIView(AdminRequiredMixin, View):
    """Activity data API"""
    
    def get(self, request):
        days = int(request.GET.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get login activity
        login_data = []
        current_date = start_date
        while current_date <= end_date:
            count = LoginHistory.objects.filter(
                login_time__date=current_date
            ).count()
            login_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'logins': count
            })
            current_date += timedelta(days=1)
        
        return JsonResponse({'login_activity': login_data}) 