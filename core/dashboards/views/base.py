"""
Base views for dashboards
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, Avg
from core.models import UserProfile, Course, Assignment, Grade
from django.utils import timezone
from django.db import models


class DashboardMixin(LoginRequiredMixin):
    """Base mixin cho tất cả dashboard views"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions trước khi render view"""
        if not self.has_permission():
            raise PermissionDenied("Bạn không có quyền truy cập trang này.")
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self):
        """Override trong subclass để check quyền cụ thể"""
        return self.request.user.is_authenticated
    
    def get_user_profile(self):
        """Lấy user profile của user hiện tại"""
        if hasattr(self.request.user, 'profile'):
            return self.request.user.profile
        return None
    
    def get_user_role(self):
        """Lấy role của user hiện tại"""
        profile = self.get_user_profile()
        if profile and hasattr(profile, 'role'):
            return profile.role  # role đã là string trong UserProfile model
        return None


class BaseDashboardView(DashboardMixin, TemplateView):
    """Base view cho tất cả dashboard"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user_profile': self.get_user_profile(),
            'user_role': self.get_user_role(),
            'dashboard_type': self.get_dashboard_type(),
            'page_title': self.get_page_title(),
            'breadcrumb': self.get_breadcrumb(),
        })
        return context
    
    def get_dashboard_type(self):
        """Override trong subclass"""
        return 'base'
    
    def get_page_title(self):
        """Override trong subclass"""
        return 'Dashboard'
    
    def get_breadcrumb(self):
        """Override trong subclass"""
        return [{'title': 'Dashboard', 'url': '#'}]


class AjaxResponseMixin:
    """Mixin để handle Ajax requests"""
    
    def dispatch(self, request, *args, **kwargs):
        self.is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.is_ajax:
            data = {
                'success': True,
                'message': 'Thao tác thành công!',
                'redirect_url': self.get_success_url() if hasattr(self, 'get_success_url') else None
            }
            return JsonResponse(data)
        return response
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.is_ajax:
            data = {
                'success': False,
                'errors': form.errors,
                'message': 'Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.'
            }
            return JsonResponse(data, status=400)
        return response


class StatisticsMixin:
    """Mixin cung cấp các thống kê cơ bản"""
    
    def get_course_statistics(self, user=None):
        """Thống kê môn học"""
        if user is None:
            user = self.request.user
            
        stats = {}
        
        # Thống kê cho sinh viên
        if self.get_user_role() == 'student':
            enrollments = user.enrollments.select_related('course')
            stats.update({
                'total_courses': enrollments.count(),
                'active_courses': enrollments.filter(course__status='active').count(),
                'completed_courses': enrollments.filter(status='completed').count(),
                'failed_courses': enrollments.filter(status='failed').count(),
            })
        
        # Thống kê cho giảng viên
        elif self.get_user_role() == 'teacher':
            courses = user.teaching_courses.all()
            stats.update({
                'total_courses': courses.count(),
                'active_courses': courses.filter(status='active').count(),
                'completed_courses': courses.filter(status='completed').count(),
                'total_students': courses.aggregate(
                    total=Count('students', distinct=True)
                )['total'] or 0,
            })
        
        return stats
    
    def get_assignment_statistics(self, user=None):
        """Thống kê bài tập"""
        if user is None:
            user = self.request.user
            
        stats = {}
        
        if self.get_user_role() == 'student':
            # Lấy assignments từ các courses mà student đã enroll
            enrolled_courses = Course.objects.filter(
                enrollments__student=user,
                enrollments__status='enrolled'
            )
            assignments = Assignment.objects.filter(course__in=enrolled_courses)
            
            stats.update({
                'total_assignments': assignments.count(),
                'pending_assignments': assignments.filter(
                    status='submission_open',
                    due_date__gte=timezone.now()
                ).count(),
                'overdue_assignments': assignments.filter(
                    status='submission_open',
                    due_date__lt=timezone.now()
                ).count(),
                'completed_assignments': assignments.filter(
                    submissions__student=user,
                    submissions__status='submitted'
                ).count(),
            })
        
        elif self.get_user_role() == 'teacher':
            assignments = Assignment.objects.filter(course__teacher=user)
            stats.update({
                'total_assignments': assignments.count(),
                'active_assignments': assignments.filter(status='submission_open').count(),
                'graded_assignments': assignments.filter(status='graded').count(),
                'pending_grading': assignments.filter(
                    status='submission_closed'
                ).count(),
            })
        
        return stats
    
    def get_grade_statistics(self, user=None):
        """Thống kê điểm số"""
        if user is None:
            user = self.request.user
            
        stats = {}
        
        if self.get_user_role() == 'student':
            grades = Grade.objects.filter(student=user)
            if grades.exists():
                avg_score = grades.aggregate(avg=Avg('score'))['avg']
                stats.update({
                    'total_grades': grades.count(),
                    'average_score': round(avg_score, 2) if avg_score else 0,
                    'highest_score': grades.aggregate(max_score=models.Max('score'))['max_score'] or 0,
                    'lowest_score': grades.aggregate(min_score=models.Min('score'))['min_score'] or 0,
                })
        
        elif self.get_user_role() == 'teacher':
            grades = Grade.objects.filter(course__teacher=user)
            stats.update({
                'total_grades_given': grades.count(),
                'students_graded': grades.values('student').distinct().count(),
                'average_class_score': round(
                    grades.aggregate(avg=Avg('score'))['avg'] or 0, 2
                ),
            })
        
        return stats 