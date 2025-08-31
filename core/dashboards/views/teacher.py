"""
Teacher Dashboard Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Avg, Count, Sum, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.forms import formset_factory
from django.contrib.auth.models import User

from .base import BaseDashboardView, AjaxResponseMixin, StatisticsMixin
from core.models import Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, Note, Tag
from core.forms import CourseForm, AssignmentForm, GradeForm


class TeacherDashboardView(BaseDashboardView, StatisticsMixin):
    """Trang chủ dashboard cho giảng viên"""
    template_name = 'dashboards/teacher/dashboard.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_dashboard_type(self):
        return 'teacher'
    
    def get_page_title(self):
        return 'Dashboard Giảng Viên'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê tổng quan
        context.update({
            'course_stats': self.get_course_statistics(),
            'assignment_stats': self.get_assignment_statistics(),
            'grade_stats': self.get_grade_statistics(),
            'student_stats': self.get_student_statistics(),
        })
        
        # Dữ liệu gần đây
        context.update({
            'active_courses': self.get_active_courses(),
            'pending_assignments': self.get_pending_assignments(),
            'recent_submissions': self.get_recent_submissions(),
            'grading_queue': self.get_grading_queue(),
            'today_schedule': self.get_today_schedule(),
        })
        
        return context
    
    def get_student_statistics(self):
        """Thống kê sinh viên"""
        courses = Course.objects.filter(teacher=self.request.user)
        total_students = CourseEnrollment.objects.filter(
            course__in=courses,
            status='enrolled'
        ).count()
        
        active_students = CourseEnrollment.objects.filter(
            course__in=courses,
            status='enrolled',
            course__status='active'
        ).count()
        
        return {
            'total_students': total_students,
            'active_students': active_students,
        }
    
    def get_active_courses(self):
        """Lấy các môn học đang hoạt động"""
        return Course.objects.filter(
            teacher=self.request.user,
            status='active'
        ).order_by('start_date')[:5]
    
    def get_pending_assignments(self):
        """Lấy bài tập cần xử lý"""
        return Assignment.objects.filter(
            course__teacher=self.request.user,
            status__in=['draft', 'submission_closed']
        ).select_related('course').order_by('due_date')[:5]
    
    def get_recent_submissions(self):
        """Lấy bài nộp gần đây"""
        teacher_assignments = Assignment.objects.filter(
            course__teacher=self.request.user
        )
        
        return AssignmentSubmission.objects.filter(
            assignment__in=teacher_assignments,
            status='submitted'
        ).select_related(
            'assignment', 'assignment__course', 'student'
        ).order_by('-submitted_at')[:5]
    
    def get_grading_queue(self):
        """Lấy danh sách bài cần chấm điểm"""
        teacher_assignments = Assignment.objects.filter(
            course__teacher=self.request.user
        )
        
        return AssignmentSubmission.objects.filter(
            assignment__in=teacher_assignments,
            status='submitted',
            grades__isnull=True
        ).select_related(
            'assignment', 'assignment__course', 'student'
        ).order_by('submitted_at')[:10]
    
    def get_today_schedule(self):
        """Lấy lịch dạy hôm nay"""
        today = timezone.now().date()
        
        return Course.objects.filter(
            teacher=self.request.user,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        )


class TeacherCourseView(BaseDashboardView, AjaxResponseMixin):
    """Quản lý môn học của giảng viên"""
    template_name = 'dashboards/teacher/courses.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_page_title(self):
        return 'Quản Lý Môn Học'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/teacher/'},
            {'title': 'Môn Học', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy danh sách môn học
        courses = Course.objects.filter(
            teacher=self.request.user
        ).prefetch_related('enrollments').order_by('-created_at')
        
        # Phân loại theo trạng thái
        active_courses = courses.filter(status='active')
        upcoming_courses = courses.filter(status='upcoming')
        completed_courses = courses.filter(status='completed')
        
        # Thống kê
        course_stats = {
            'total': courses.count(),
            'active': active_courses.count(),
            'upcoming': upcoming_courses.count(),
            'completed': completed_courses.count(),
        }
        
        context.update({
            'courses': courses,
            'active_courses': active_courses,
            'upcoming_courses': upcoming_courses,
            'completed_courses': completed_courses,
            'course_stats': course_stats,
            'course_form': CourseForm(),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Tạo môn học mới"""
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            
            if self.is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Môn học đã được tạo thành công!',
                    'course_id': course.id
                })
            else:
                messages.success(request, 'Môn học đã được tạo thành công!')
                return redirect('core:teacher_courses')
        
        if self.is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        return self.get(request, *args, **kwargs)


class TeacherCourseDetailView(BaseDashboardView):
    """Chi tiết môn học cho giảng viên"""
    template_name = 'dashboards/teacher/course_detail.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_page_title(self):
        course = self.get_course()
        return f'Môn học: {course.name}' if course else 'Chi tiết môn học'
    
    def get_breadcrumb(self):
        course = self.get_course()
        return [
            {'title': 'Dashboard', 'url': '/dashboard/teacher/'},
            {'title': 'Môn Học', 'url': '/dashboard/teacher/courses/'},
            {'title': course.name if course else 'Chi tiết', 'url': '#'}
        ]
    
    def get_course(self):
        """Lấy course object"""
        if not hasattr(self, '_course'):
            course_id = self.kwargs.get('course_id')
            self._course = get_object_or_404(
                Course,
                id=course_id,
                teacher=self.request.user
            )
        return self._course
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_course()
        
        # Lấy enrollments
        enrollments = CourseEnrollment.objects.filter(
            course=course
        ).select_related('student').order_by('-enrolled_at')
        
        # Lấy assignments
        assignments = Assignment.objects.filter(
            course=course
        ).order_by('-created_at')
        
        # Lấy grades
        grades = Grade.objects.filter(
            course=course
        ).select_related('student', 'assignment')
        
        # Thống kê
        enrollment_stats = {
            'total': enrollments.count(),
            'enrolled': enrollments.filter(status='enrolled').count(),
            'completed': enrollments.filter(status='completed').count(),
            'dropped': enrollments.filter(status='dropped').count(),
        }
        
        assignment_stats = {
            'total': assignments.count(),
            'published': assignments.filter(status='published').count(),
            'submission_open': assignments.filter(status='submission_open').count(),
            'graded': assignments.filter(status='graded').count(),
        }
        
        grade_stats = {}
        if grades.exists():
            grade_stats = {
                'average': grades.aggregate(avg=Avg('score'))['avg'],
                'highest': grades.aggregate(max_score=Max('score'))['max_score'],
                'lowest': grades.aggregate(min_score=Min('score'))['min_score'],
                'total_grades': grades.count(),
            }
        
        context.update({
            'course': course,
            'enrollments': enrollments,
            'assignments': assignments,
            'grades': grades,
            'enrollment_stats': enrollment_stats,
            'assignment_stats': assignment_stats,
            'grade_stats': grade_stats,
        })
        
        return context


class TeacherAssignmentView(BaseDashboardView, AjaxResponseMixin):
    """Quản lý bài tập của giảng viên"""
    template_name = 'dashboards/teacher/assignments.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_page_title(self):
        return 'Quản Lý Bài Tập'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/teacher/'},
            {'title': 'Bài Tập', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy tất cả assignments
        assignments = Assignment.objects.filter(
            course__teacher=self.request.user
        ).select_related('course').order_by('-created_at')
        
        # Phân loại theo trạng thái
        draft_assignments = assignments.filter(status='draft')
        published_assignments = assignments.filter(status='published')
        open_assignments = assignments.filter(status='submission_open')
        closed_assignments = assignments.filter(status='submission_closed')
        graded_assignments = assignments.filter(status='graded')
        
        # Thống kê submissions
        submission_stats = {}
        for assignment in assignments:
            submissions = AssignmentSubmission.objects.filter(assignment=assignment)
            submission_stats[assignment.id] = {
                'total': submissions.count(),
                'submitted': submissions.filter(status='submitted').count(),
                'graded': submissions.filter(grades__isnull=False).count(),
            }
        
        # Thống kê tổng
        assignment_stats = {
            'total': assignments.count(),
            'draft': draft_assignments.count(),
            'published': published_assignments.count(),
            'open': open_assignments.count(),
            'closed': closed_assignments.count(),
            'graded': graded_assignments.count(),
        }
        
        # Lấy courses cho form
        teacher_courses = Course.objects.filter(teacher=self.request.user)
        
        context.update({
            'assignments': assignments,
            'draft_assignments': draft_assignments,
            'published_assignments': published_assignments,
            'open_assignments': open_assignments,
            'closed_assignments': closed_assignments,
            'graded_assignments': graded_assignments,
            'assignment_stats': assignment_stats,
            'submission_stats': submission_stats,
            'teacher_courses': teacher_courses,
            'assignment_form': AssignmentForm(),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Tạo bài tập mới"""
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            
            if self.is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Bài tập đã được tạo thành công!',
                    'assignment_id': assignment.id
                })
            else:
                messages.success(request, 'Bài tập đã được tạo thành công!')
                return redirect('core:teacher_assignments')
        
        if self.is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        return self.get(request, *args, **kwargs)


class TeacherGradeView(BaseDashboardView, AjaxResponseMixin):
    """Quản lý điểm số của giảng viên"""
    template_name = 'dashboards/teacher/grades.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_page_title(self):
        return 'Quản Lý Điểm Số'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/teacher/'},
            {'title': 'Điểm Số', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy tất cả grades
        grades = Grade.objects.filter(
            course__teacher=self.request.user
        ).select_related('student', 'course', 'assignment').order_by('-created_at')
        
        # Phân loại theo môn học
        grades_by_course = {}
        for grade in grades:
            course_id = grade.course.id
            if course_id not in grades_by_course:
                grades_by_course[course_id] = {
                    'course': grade.course,
                    'grades': [],
                    'students': set(),
                    'average': 0,
                    'total_grades': 0
                }
            grades_by_course[course_id]['grades'].append(grade)
            grades_by_course[course_id]['students'].add(grade.student.id)
        
        # Tính thống kê cho mỗi môn
        for course_data in grades_by_course.values():
            course_grades = course_data['grades']
            if course_grades:
                total_score = sum(g.score for g in course_grades)
                course_data['average'] = round(total_score / len(course_grades), 2)
                course_data['total_grades'] = len(course_grades)
                course_data['students_count'] = len(course_data['students'])
        
        # Lấy submissions cần chấm điểm
        pending_submissions = AssignmentSubmission.objects.filter(
            assignment__course__teacher=self.request.user,
            status='submitted',
            grades__isnull=True
        ).select_related('assignment', 'assignment__course', 'student')
        
        # Thống kê tổng
        grade_stats = {
            'total_grades': grades.count(),
            'pending_submissions': pending_submissions.count(),
            'courses_with_grades': len(grades_by_course),
            'average_score': round(grades.aggregate(avg=Avg('score'))['avg'] or 0, 2),
        }
        
        context.update({
            'grades': grades,
            'grades_by_course': grades_by_course,
            'pending_submissions': pending_submissions,
            'grade_stats': grade_stats,
            'grade_form': GradeForm(),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Nhập điểm mới"""
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.created_by = request.user
            grade.save()
            
            if self.is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Điểm đã được nhập thành công!',
                    'grade_id': grade.id
                })
            else:
                messages.success(request, 'Điểm đã được nhập thành công!')
                return redirect('core:teacher_grades')
        
        if self.is_ajax:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        return self.get(request, *args, **kwargs)


class TeacherStudentView(BaseDashboardView):
    """Quản lý sinh viên của giảng viên"""
    template_name = 'dashboards/teacher/students.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_page_title(self):
        return 'Quản Lý Sinh Viên'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/teacher/'},
            {'title': 'Sinh Viên', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy tất cả courses của teacher
        teacher_courses = Course.objects.filter(teacher=self.request.user)
        
        # Lấy tất cả enrollments
        enrollments = CourseEnrollment.objects.filter(
            course__in=teacher_courses
        ).select_related('student', 'course').order_by('-enrolled_at')
        
        # Phân loại theo môn học
        students_by_course = {}
        for enrollment in enrollments:
            course_id = enrollment.course.id
            if course_id not in students_by_course:
                students_by_course[course_id] = {
                    'course': enrollment.course,
                    'enrollments': [],
                    'students_count': 0
                }
            students_by_course[course_id]['enrollments'].append(enrollment)
        
        # Đếm sinh viên cho mỗi môn
        for course_data in students_by_course.values():
            course_data['students_count'] = len(course_data['enrollments'])
        
        # Lấy thống kê sinh viên
        unique_students = User.objects.filter(
            enrollments__course__in=teacher_courses
        ).distinct()
        
        # Phân tích hiệu suất sinh viên
        student_performance = {}
        for student in unique_students:
            grades = Grade.objects.filter(
                student=student,
                course__teacher=self.request.user
            )
            
            if grades.exists():
                avg_score = grades.aggregate(avg=Avg('score'))['avg']
                student_performance[student.id] = {
                    'student': student,
                    'average_score': round(avg_score, 2),
                    'total_grades': grades.count(),
                    'courses': grades.values('course').distinct().count(),
                }
        
        # Thống kê tổng
        student_stats = {
            'total_enrollments': enrollments.count(),
            'unique_students': unique_students.count(),
            'active_enrollments': enrollments.filter(
                status='enrolled',
                course__status='active'
            ).count(),
            'completed_enrollments': enrollments.filter(status='completed').count(),
        }
        
        context.update({
            'enrollments': enrollments,
            'students_by_course': students_by_course,
            'unique_students': unique_students,
            'student_performance': student_performance,
            'student_stats': student_stats,
            'teacher_courses': teacher_courses,
        })
        
        return context


class TeacherGradingView(BaseDashboardView, AjaxResponseMixin):
    """Trang chấm điểm hàng loạt"""
    template_name = 'dashboards/teacher/grading.html'
    
    def has_permission(self):
        return (self.request.user.is_authenticated and 
                self.get_user_role() == 'teacher')
    
    def get_page_title(self):
        return 'Chấm Điểm Hàng Loạt'
    
    def get_breadcrumb(self):
        return [
            {'title': 'Dashboard', 'url': '/dashboard/teacher/'},
            {'title': 'Chấm Điểm', 'url': '#'}
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy assignment từ URL parameter
        assignment_id = self.request.GET.get('assignment')
        selected_assignment = None
        submissions = []
        
        if assignment_id:
            try:
                selected_assignment = Assignment.objects.get(
                    id=assignment_id,
                    course__teacher=self.request.user
                )
                submissions = AssignmentSubmission.objects.filter(
                    assignment=selected_assignment,
                    status='submitted'
                ).select_related('student').order_by('student__last_name')
                
            except Assignment.DoesNotExist:
                messages.error(self.request, 'Bài tập không tồn tại hoặc bạn không có quyền truy cập.')
        
        # Lấy danh sách assignments có thể chấm điểm
        gradable_assignments = Assignment.objects.filter(
            course__teacher=self.request.user,
            status__in=['submission_closed', 'graded']
        ).select_related('course')
        
        context.update({
            'gradable_assignments': gradable_assignments,
            'selected_assignment': selected_assignment,
            'submissions': submissions,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Xử lý chấm điểm hàng loạt"""
        assignment_id = request.POST.get('assignment_id')
        
        try:
            assignment = Assignment.objects.get(
                id=assignment_id,
                course__teacher=request.user
            )
        except Assignment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Bài tập không tồn tại.'
            }, status=400)
        
        # Xử lý điểm cho từng submission
        graded_count = 0
        errors = []
        
        for key, value in request.POST.items():
            if key.startswith('score_'):
                submission_id = key.replace('score_', '')
                try:
                    submission = AssignmentSubmission.objects.get(
                        id=submission_id,
                        assignment=assignment
                    )
                    score = float(value)
                    
                    # Tạo hoặc cập nhật grade
                    grade, created = Grade.objects.get_or_create(
                        student=submission.student,
                        course=assignment.course,
                        assignment=assignment,
                        submission=submission,
                        defaults={
                            'score': score,
                            'max_score': assignment.max_score,
                            'date': timezone.now().date(),
                            'created_by': request.user,
                            'grade_type': 'assignment',
                        }
                    )
                    
                    if not created:
                        grade.score = score
                        grade.created_by = request.user
                        grade.save()
                    
                    graded_count += 1
                    
                except (AssignmentSubmission.DoesNotExist, ValueError) as e:
                    errors.append(f'Lỗi với submission {submission_id}: {str(e)}')
        
        if self.is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'Đã chấm điểm thành công cho {graded_count} bài nộp.',
                'graded_count': graded_count,
                'errors': errors
            })
        
        messages.success(request, f'Đã chấm điểm thành công cho {graded_count} bài nộp.')
        if errors:
            for error in errors:
                messages.warning(request, error)
        
        return redirect('core:teacher_grading') 