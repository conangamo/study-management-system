"""
Student Dashboard Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q, Avg, Count, Sum, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse_lazy

from .base import BaseDashboardView, AjaxResponseMixin, StatisticsMixin
from core.models import Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, Note, Tag
from core.forms import NoteForm, AssignmentSubmissionForm


class StudentDashboardView(BaseDashboardView, StatisticsMixin):
    """Trang chủ dashboard cho sinh viên"""
    template_name = 'dashboards/student/dashboard.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'student')
    
    def get_dashboard_type(self):
        return 'student'
    
    def get_page_title(self):
        return 'Dashboard Sinh Viên'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê tổng quan
        context.update({
            'course_stats': self.get_course_statistics(),
            'assignment_stats': self.get_assignment_statistics(),
            'grade_stats': self.get_grade_statistics(),
        })
        
        # Dữ liệu gần đây
        context.update({
            'recent_courses': self.get_recent_courses(),
            'upcoming_assignments': self.get_upcoming_assignments(),
            'recent_grades': self.get_recent_grades(),
            'quick_notes': self.get_quick_notes(),
            'schedule_today': self.get_today_schedule(),
        })
        
        return context
    
    def get_recent_courses(self):
        """Lấy các môn học gần đây"""
        return Course.objects.filter(
            enrollments__student=self.request.user,
            enrollments__status='enrolled'
        ).select_related('teacher').order_by('-start_date')[:5]
    
    def get_upcoming_assignments(self):
        """Lấy bài tập sắp đến hạn"""
        enrolled_courses = Course.objects.filter(
            enrollments__student=self.request.user,
            enrollments__status='enrolled'
        )
        
        return Assignment.objects.filter(
            course__in=enrolled_courses,
            status='submission_open',
            due_date__gte=timezone.now()
        ).select_related('course').order_by('due_date')[:5]
    
    def get_recent_grades(self):
        """Lấy điểm số mới nhất"""
        return Grade.objects.filter(
            student=self.request.user
        ).select_related('course', 'assignment').order_by('-created_at')[:5]
    
    def get_quick_notes(self):
        """Lấy ghi chú nhanh"""
        return Note.objects.filter(
            user=self.request.user,
            is_pinned=True
        ).order_by('-updated_at')[:3]
    
    def get_today_schedule(self):
        """Lấy lịch học hôm nay"""
        today = timezone.now().date()
        
        # Giả sử có schedule trong Course model hoặc tạo riêng
        enrolled_courses = Course.objects.filter(
            enrollments__student=self.request.user,
            enrollments__status='enrolled',
            status='active'
        )
        
        return enrolled_courses.filter(
            start_date__lte=today,
            end_date__gte=today
        )


class StudentCourseView(BaseDashboardView, StatisticsMixin):
    """Quản lý môn học của sinh viên"""
    template_name = 'dashboards/student/courses.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'student')
    
    def get_page_title(self):
        return 'Môn Học Của Tôi'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/student/'},
            {'title': 'Môn Học', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy danh sách môn học
        enrollments = CourseEnrollment.objects.filter(
            student=self.request.user
        ).select_related('course', 'course__teacher').order_by('-enrolled_at')
        
        # Phân loại theo trạng thái
        active_courses = enrollments.filter(status='enrolled', course__status='active')
        completed_courses = enrollments.filter(status='completed')
        upcoming_courses = enrollments.filter(course__status='upcoming')
        
        context.update({
            'all_enrollments': enrollments,
            'active_courses': active_courses,
            'completed_courses': completed_courses,
            'upcoming_courses': upcoming_courses,
            'course_stats': self.get_course_statistics(),
        })
        
        return context


class StudentCourseDetailView(BaseDashboardView):
    """Chi tiết môn học cho sinh viên"""
    template_name = 'dashboards/student/course_detail.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'student')
    
    def get_page_title(self):
        course = self.get_course()
        return f'Môn học: {course.name}' if course else 'Chi tiết môn học'
    
    def get_breadcrumb(self):
        course = self.get_course()
        return [
            {'title': 'Dashboard', 'url': '/dashboard/student/'},
            {'title': 'Môn Học', 'url': '/dashboard/student/courses/'},
            {'title': course.name if course else 'Chi tiết', 'url': '#'}
        ]
    
    def get_course(self):
        """Lấy course object"""
        if not hasattr(self, '_course'):
            course_id = self.kwargs.get('course_id')
            self._course = get_object_or_404(
                Course,
                id=course_id,
                enrollments__student=self.request.user
            )
        return self._course
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_course()
        
        # Lấy enrollment info
        enrollment = CourseEnrollment.objects.get(
            student=self.request.user,
            course=course
        )
        
        # Lấy assignments
        assignments = Assignment.objects.filter(
            course=course
        ).order_by('-created_at')
        
        # Lấy grades
        grades = Grade.objects.filter(
            student=self.request.user,
            course=course
        ).select_related('assignment')
        
        # Thống kê
        assignment_stats = {
            'total': assignments.count(),
            'completed': assignments.filter(
                submissions__student=self.request.user,
                submissions__status='submitted'
            ).count(),
            'pending': assignments.filter(
                status='submission_open',
                due_date__gte=timezone.now()
            ).count(),
            'overdue': assignments.filter(
                status='submission_open',
                due_date__lt=timezone.now()
            ).count(),
        }
        
        grade_stats = {}
        if grades.exists():
            grade_stats = {
                'average': grades.aggregate(avg=Avg('score'))['avg'],
                'highest': grades.aggregate(max_score=Max('score'))['max_score'],
                'total_grades': grades.count(),
            }
        
        context.update({
            'course': course,
            'enrollment': enrollment,
            'assignments': assignments,
            'grades': grades,
            'assignment_stats': assignment_stats,
            'grade_stats': grade_stats,
        })
        
        return context


class StudentAssignmentView(BaseDashboardView):
    """Quản lý bài tập của sinh viên"""
    template_name = 'dashboards/student/assignments.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'student')
    
    def get_page_title(self):
        return 'Bài Tập Của Tôi'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/student/'},
            {'title': 'Bài Tập', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy enrolled courses
        enrolled_courses = Course.objects.filter(
            enrollments__student=self.request.user,
            enrollments__status='enrolled'
        )
        
        # Lấy tất cả assignments
        all_assignments = Assignment.objects.filter(
            course__in=enrolled_courses
        ).select_related('course').order_by('-due_date')
        
        # Phân loại assignments
        pending_assignments = all_assignments.filter(
            status='submission_open',
            due_date__gte=timezone.now()
        )
        
        overdue_assignments = all_assignments.filter(
            status='submission_open',
            due_date__lt=timezone.now()
        )
        
        completed_assignments = all_assignments.filter(
            submissions__student=self.request.user,
            submissions__status='submitted'
        )
        
        upcoming_assignments = all_assignments.filter(
            status='published',
            due_date__gte=timezone.now()
        ).exclude(
            id__in=pending_assignments.values_list('id', flat=True)
        )
        
        # Thống kê
        assignment_stats = {
            'total': all_assignments.count(),
            'pending': pending_assignments.count(),
            'overdue': overdue_assignments.count(),
            'completed': completed_assignments.count(),
            'upcoming': upcoming_assignments.count(),
        }
        
        context.update({
            'all_assignments': all_assignments,
            'pending_assignments': pending_assignments,
            'overdue_assignments': overdue_assignments,
            'completed_assignments': completed_assignments,
            'upcoming_assignments': upcoming_assignments,
            'assignment_stats': assignment_stats,
        })
        
        return context


class StudentGradeView(BaseDashboardView, StatisticsMixin):
    """Xem điểm số và phân tích cho sinh viên"""
    template_name = 'dashboards/student/grades.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'student')
    
    def get_page_title(self):
        return 'Điểm Số Của Tôi'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/student/'},
            {'title': 'Điểm Số', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy tất cả grades
        grades = Grade.objects.filter(
            student=self.request.user
        ).select_related('course', 'assignment', 'created_by').order_by('-date')
        
        # Phân loại theo môn học
        grades_by_course = {}
        for grade in grades:
            course_id = grade.course.id
            if course_id not in grades_by_course:
                grades_by_course[course_id] = {
                    'course': grade.course,
                    'grades': [],
                    'average': 0,
                    'total_grades': 0
                }
            grades_by_course[course_id]['grades'].append(grade)
        
        # Tính average cho mỗi môn
        for course_data in grades_by_course.values():
            course_grades = course_data['grades']
            if course_grades:
                total_score = sum(g.score for g in course_grades)
                course_data['average'] = round(total_score / len(course_grades), 2)
                course_data['total_grades'] = len(course_grades)
        
        # Thống kê tổng
        grade_stats = self.get_grade_statistics()
        
        # Dữ liệu cho chart
        chart_data = self.get_grade_chart_data(grades)
        
        context.update({
            'grades': grades,
            'grades_by_course': grades_by_course,
            'grade_stats': grade_stats,
            'chart_data': chart_data,
        })
        
        return context
    
    def get_grade_chart_data(self, grades):
        """Chuẩn bị dữ liệu cho biểu đồ"""
        # Dữ liệu theo thời gian
        monthly_data = {}
        for grade in grades:
            month_key = grade.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(float(grade.score))
        
        # Tính average theo tháng
        chart_labels = []
        chart_values = []
        for month in sorted(monthly_data.keys()):
            chart_labels.append(month)
            avg_score = sum(monthly_data[month]) / len(monthly_data[month])
            chart_values.append(round(avg_score, 2))
        
        return {
            'labels': chart_labels,
            'values': chart_values,
        }


class StudentNoteView(BaseDashboardView, AjaxResponseMixin):
    """Quản lý ghi chú của sinh viên"""
    template_name = 'dashboards/student/notes.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'student')
    
    def get_page_title(self):
        return 'Ghi Chú Của Tôi'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/student/'},
            {'title': 'Ghi Chú', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy tất cả notes
        notes = Note.objects.filter(
            user=self.request.user
        ).prefetch_related('tags').order_by('-updated_at')
        
        # Lấy tags
        tags = Tag.objects.filter(
            notes__user=self.request.user
        ).distinct().order_by('name')
        
        # Filter theo tag nếu có
        tag_filter = self.request.GET.get('tag')
        if tag_filter:
            notes = notes.filter(tags__name=tag_filter)
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            notes = notes.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        # Phân loại
        pinned_notes = notes.filter(is_pinned=True)
        recent_notes = notes.filter(is_pinned=False)[:10]
        
        context.update({
            'notes': notes,
            'pinned_notes': pinned_notes,
            'recent_notes': recent_notes,
            'tags': tags,
            'selected_tag': tag_filter,
            'search_query': search_query,
            'note_form': NoteForm(),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Tạo note mới"""
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            form.save_m2m()
            
            if self.is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Ghi chú đã được tạo thành công!',
                    'note_id': note.id
                })
            else:
                messages.success(request, 'Ghi chú đã được tạo thành công!')
                return redirect('core:student_notes')
        
        if self.is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        # Nếu form invalid và không phải ajax, render lại page
        return self.get(request, *args, **kwargs) 