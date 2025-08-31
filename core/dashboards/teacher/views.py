"""
Teacher Dashboard Views
- Course Management: Create, Edit, Delete courses
- Assignment Management: Create assignments, track submissions  
- Grade Management: Enter grades, view statistics
- Student Management: View student list
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView
)
from django.contrib import messages
from django.db.models import Q, Count, Avg, Max, Min
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import json

from core.models.study import Course, Grade
from core.models.assignment import Assignment, AssignmentSubmission
from core.models.user import UserProfile
from .forms import (
    TeacherCourseForm, TeacherAssignmentForm, TeacherGradeForm,
    TeacherBulkGradeForm, TeacherAssignmentGradingForm
)
from .mixins import TeacherRequiredMixin
from django.core.exceptions import PermissionDenied


class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    """Teacher Dashboard main view"""
    template_name = 'dashboards/teacher/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Overview statistics
        context.update({
            'total_courses': Course.objects.filter(
                Q(teacher=user) | Q(assistant_teachers=user)
            ).distinct().count(),
            'active_courses': Course.objects.filter(
                Q(teacher=user) | Q(assistant_teachers=user),
                status='active'
            ).distinct().count(),
            'total_assignments': Assignment.objects.filter(
                Q(course__teacher=user) | Q(course__assistant_teachers=user)
            ).distinct().count(),
            'pending_submissions': AssignmentSubmission.objects.filter(
                Q(assignment__course__teacher=user) | Q(assignment__course__assistant_teachers=user),
                status='submitted'
            ).distinct().count(),
            'total_students': User.objects.filter(
                Q(enrolled_courses__teacher=user) | Q(enrolled_courses__assistant_teachers=user),
                profile__role='student'
            ).distinct().count(),
        })
        
        # Recent courses
        context['recent_courses'] = Course.objects.filter(
            Q(teacher=user) | Q(assistant_teachers=user)
        ).distinct().order_by('-created_at')[:5]
        
        # Recent assignments
        context['recent_assignments'] = Assignment.objects.filter(
            Q(course__teacher=user) | Q(course__assistant_teachers=user)
        ).distinct().order_by('-created_at')[:5]
        
        # Pending submissions
        context['pending_submissions_list'] = AssignmentSubmission.objects.filter(
            Q(assignment__course__teacher=user) | Q(assignment__course__assistant_teachers=user),
            status__in=['submitted', 'late']
        ).distinct().order_by('-submitted_at')[:5]
        
        return context


# =============================================================================
# COURSE MANAGEMENT VIEWS
# =============================================================================

class TeacherCourseListView(TeacherRequiredMixin, ListView):
    """List all courses taught by teacher"""
    model = Course
    template_name = 'dashboards/teacher/course/list.html'
    context_object_name = 'courses'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        return Course.objects.filter(Q(teacher=user) | Q(assistant_teachers=user)).distinct().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_courses'] = self.get_queryset().filter(status='active').count()
        context['upcoming_courses'] = self.get_queryset().filter(status='upcoming').count()
        context['completed_courses'] = self.get_queryset().filter(status='completed').count()
        return context


class TeacherCourseDetailView(TeacherRequiredMixin, DetailView):
    """Course detail view"""
    model = Course
    template_name = 'dashboards/teacher/course/detail.html'
    context_object_name = 'course'
    
    def get_queryset(self):
        return Course.objects.filter(
            Q(teacher=self.request.user) | Q(assistant_teachers=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Course statistics
        context.update({
            'student_count': course.students.count(),
            'assignment_count': course.assignments.count(),
            'recent_assignments': course.assignments.order_by('-created_at')[:5],
            'enrolled_students': course.students.filter(profile__role='student')[:10],
        })
        
        # Grade statistics
        grades = Grade.objects.filter(course=course)
        if grades.exists():
            context.update({
                'average_grade': grades.aggregate(avg=Avg('score'))['avg'],
                'grade_count': grades.count(),
            })
        
        return context


class TeacherCourseCreateView(TeacherRequiredMixin, CreateView):
    """Create new course"""
    model = Course
    form_class = TeacherCourseForm
    template_name = 'dashboards/teacher/course/create.html'
    
    def form_valid(self, form):
        # Restrict to admin only
        if not (self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')):
            raise PermissionDenied('Chỉ admin mới có thể thêm môn học.')
        messages.success(self.request, 'Môn học đã được tạo thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:teacher:course_detail', kwargs={'pk': self.object.pk})


class TeacherCourseUpdateView(TeacherRequiredMixin, UpdateView):
    """Update course"""
    model = Course
    form_class = TeacherCourseForm
    template_name = 'dashboards/teacher/course/edit.html'
    
    def get_queryset(self):
        return Course.objects.filter(
            Q(teacher=self.request.user) | Q(assistant_teachers=self.request.user)
        ).distinct()
    
    def form_valid(self, form):
        # Restrict to admin only
        if not (self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin')):
            raise PermissionDenied('Chỉ admin mới có thể sửa môn học.')
        messages.success(self.request, 'Môn học đã được cập nhật thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:teacher:course_detail', kwargs={'pk': self.object.pk})


class TeacherCourseDeleteView(TeacherRequiredMixin, DeleteView):
    """Delete course"""
    model = Course
    template_name = 'dashboards/teacher/course/delete.html'
    success_url = reverse_lazy('dashboards:teacher:course_list')
    
    def get_queryset(self):
        return Course.objects.filter(
            Q(teacher=self.request.user) | Q(assistant_teachers=self.request.user)
        ).distinct()
    
    def delete(self, request, *args, **kwargs):
        # Restrict to admin only
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            raise PermissionDenied('Chỉ admin mới có thể xóa môn học.')
        messages.success(request, 'Môn học đã được xóa thành công!')
        return super().delete(request, *args, **kwargs)


class TeacherCourseStudentsView(TeacherRequiredMixin, DetailView):
    """View students enrolled in course"""
    model = Course
    template_name = 'dashboards/teacher/course/students.html'
    context_object_name = 'course'
    
    def get_queryset(self):
        return Course.objects.filter(
            Q(teacher=self.request.user) | Q(assistant_teachers=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Get enrolled students with their grades
        students = User.objects.filter(
            enrolled_courses=course,
            profile__role='student'
        ).select_related('profile').prefetch_related('grades')
        
        # Calculate grade statistics for each student
        student_data = []
        for student in students:
            student_grades = Grade.objects.filter(course=course, student=student)
            student_data.append({
                'student': student,
                'grade_count': student_grades.count(),
                'average_grade': student_grades.aggregate(avg=Avg('score'))['avg'] or 0,
                'last_submission': AssignmentSubmission.objects.filter(
                    assignment__course=course,
                    student=student
                ).order_by('-submitted_at').first()
            })
        
        context['student_data'] = student_data
        return context


# =============================================================================
# ASSIGNMENT MANAGEMENT VIEWS  
# =============================================================================

class TeacherAssignmentListView(TeacherRequiredMixin, ListView):
    """List all assignments created by teacher"""
    model = Assignment
    template_name = 'dashboards/teacher/assignment/list.html'
    context_object_name = 'assignments'
    paginate_by = 10
    
    def get_queryset(self):
        return Assignment.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct().select_related('course').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context.update({
            'total_assignments': queryset.count(),
            'draft_assignments': queryset.filter(status='draft').count(),
            'active_assignments': queryset.filter(status='active').count(),
            'closed_assignments': queryset.filter(status='closed').count(),
        })
        return context


class TeacherAssignmentDetailView(TeacherRequiredMixin, DetailView):
    """Assignment detail view"""
    model = Assignment
    template_name = 'dashboards/teacher/assignment/detail.html'
    context_object_name = 'assignment'
    
    def get_queryset(self):
        return Assignment.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        
        # Submission statistics
        submissions = AssignmentSubmission.objects.filter(assignment=assignment)
        graded_count = submissions.filter(status='graded').count()
        total_count = submissions.count()
        
        context.update({
            'total_submissions': total_count,
            'graded_submissions': graded_count,
            'pending_submissions': total_count - graded_count,
            'late_submissions': submissions.filter(status='late').count(),
            'recent_submissions': submissions.order_by('-submitted_at')[:5],
        })
        
        # Grade statistics
        grades = Grade.objects.filter(assignment=assignment)
        if grades.exists():
            context.update({
                'average_grade': grades.aggregate(avg=Avg('score'))['avg'],
                'highest_grade': grades.aggregate(max=Max('score'))['max'],
                'lowest_grade': grades.aggregate(min=Min('score'))['min'],
            })
        
        return context


class TeacherAssignmentCreateView(TeacherRequiredMixin, CreateView):
    """Create new assignment"""
    model = Assignment
    form_class = TeacherAssignmentForm
    template_name = 'dashboards/teacher/assignment/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Bài tập đã được tạo thành công!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Debug form errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'Lỗi ở trường {field}: {error}')
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('dashboards:teacher:assignment_detail', kwargs={'pk': self.object.pk})


class TeacherAssignmentUpdateView(TeacherRequiredMixin, UpdateView):
    """Update assignment"""
    model = Assignment
    form_class = TeacherAssignmentForm
    template_name = 'dashboards/teacher/assignment/edit.html'
    
    def get_queryset(self):
        return Assignment.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Bài tập đã được cập nhật thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:teacher:assignment_detail', kwargs={'pk': self.object.pk})


class TeacherAssignmentDeleteView(TeacherRequiredMixin, DeleteView):
    """Delete assignment"""
    model = Assignment
    template_name = 'dashboards/teacher/assignment/delete.html'
    success_url = reverse_lazy('dashboards:teacher:assignment_list')
    
    def get_queryset(self):
        return Assignment.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Bài tập đã được xóa thành công!')
        return super().delete(request, *args, **kwargs)


class TeacherAssignmentSubmissionsView(TeacherRequiredMixin, DetailView):
    """View all submissions for an assignment"""
    model = Assignment
    template_name = 'dashboards/teacher/assignment/submissions.html'
    context_object_name = 'assignment'
    
    def get_queryset(self):
        return Assignment.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        
        # Get all submissions with student info
        submissions = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).select_related('student', 'student__profile').order_by('-submitted_at')
        
        context['submissions'] = submissions
        
        # Submission statistics
        context.update({
            'total_submissions': submissions.count(),
            'graded_count': submissions.filter(status='graded').count(),
            'pending_count': submissions.filter(status__in=['submitted', 'late']).count(),
            'late_count': submissions.filter(status='late').count(),
        })
        
        return context


class TeacherAssignmentGradingView(TeacherRequiredMixin, DetailView):
    """Grade assignment submissions"""
    model = Assignment
    template_name = 'dashboards/teacher/assignment/grading.html'
    context_object_name = 'assignment'
    
    def get_queryset(self):
        return Assignment.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        
        # Get ungraded submissions
        ungraded_submissions = AssignmentSubmission.objects.filter(
            assignment=assignment,
            status__in=['submitted', 'late']
        ).select_related('student', 'student__profile').order_by('submitted_at')
        
        context['ungraded_submissions'] = ungraded_submissions
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle grading form submission"""
        assignment = self.get_object()
        submission_id = request.POST.get('submission_id')
        score = request.POST.get('score')
        feedback = request.POST.get('feedback', '')
        
        try:
            submission = AssignmentSubmission.objects.get(
                id=submission_id,
                assignment=assignment
            )
            
            # Create or update grade
            grade, created = Grade.objects.get_or_create(
                student=submission.student,
                course=assignment.course,
                assignment=assignment,
                submission=submission,
                defaults={
                    'grade_type': 'assignment',
                    'score': float(score),
                    'max_score': assignment.max_score,
                    'weight': assignment.weight,
                    'date': timezone.now().date(),
                    'comment': feedback,
                    'created_by': request.user,
                }
            )
            
            if not created:
                grade.score = float(score)
                grade.comment = feedback
                grade.save()
            
            # Update submission status
            submission.status = 'graded'
            submission.score = float(score)
            submission.feedback = feedback
            submission.graded_at = timezone.now()
            submission.save()
            
            messages.success(request, f'Đã chấm điểm cho {submission.student.get_full_name()}')
            
        except (AssignmentSubmission.DoesNotExist, ValueError) as e:
            messages.error(request, f'Lỗi khi chấm điểm: {str(e)}')
        
        return redirect('dashboards:teacher:assignment_grading', pk=assignment.pk)


# =============================================================================
# GRADE MANAGEMENT VIEWS
# =============================================================================

class TeacherGradeListView(TeacherRequiredMixin, ListView):
    """List all grades created by teacher"""
    model = Grade
    template_name = 'dashboards/teacher/grade/list.html'
    context_object_name = 'grades'
    paginate_by = 20
    
    def get_queryset(self):
        return Grade.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct().select_related('student', 'course', 'assignment').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context.update({
            'total_grades': queryset.count(),
            'average_grade': queryset.aggregate(avg=Avg('score'))['avg'] or 0,
            'courses': Course.objects.filter(
                Q(teacher=self.request.user) | Q(assistant_teachers=self.request.user)
            ).distinct(),
        })
        return context


class TeacherGradeCreateView(TeacherRequiredMixin, CreateView):
    """Create new grade entry"""
    model = Grade
    form_class = TeacherGradeForm
    template_name = 'dashboards/teacher/grade/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Điểm đã được nhập thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:teacher:grade_list')


class TeacherGradeUpdateView(TeacherRequiredMixin, UpdateView):
    """Update grade"""
    model = Grade
    form_class = TeacherGradeForm
    template_name = 'dashboards/teacher/grade/edit.html'
    
    def get_queryset(self):
        return Grade.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Điểm đã được cập nhật thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('dashboards:teacher:grade_list')


class TeacherGradeDeleteView(TeacherRequiredMixin, DeleteView):
    """Delete grade"""
    model = Grade
    template_name = 'dashboards/teacher/grade/delete.html'
    success_url = reverse_lazy('dashboards:teacher:grade_list')
    
    def get_queryset(self):
        return Grade.objects.filter(
            Q(course__teacher=self.request.user) | Q(course__assistant_teachers=self.request.user)
        ).distinct()
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Điểm đã được xóa thành công!')
        return super().delete(request, *args, **kwargs)


class TeacherGradeStatisticsView(TeacherRequiredMixin, TemplateView):
    """View grade statistics and analytics"""
    template_name = 'dashboards/teacher/grade/statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user
        
        # Overall statistics
        all_grades = Grade.objects.filter(
            Q(course__teacher=teacher) | Q(course__assistant_teachers=teacher)
        ).distinct()
        context.update({
            'total_grades': all_grades.count(),
            'average_grade': all_grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'highest_grade': all_grades.aggregate(max=Max('score'))['max'] or 0,
            'lowest_grade': all_grades.aggregate(min=Min('score'))['min'] or 0,
        })
        
        # Grade distribution
        grade_ranges = [
            ('A+ (9.0-10)', all_grades.filter(score__gte=9.0).count()),
            ('A (8.0-8.9)', all_grades.filter(score__gte=8.0, score__lt=9.0).count()),
            ('B+ (7.0-7.9)', all_grades.filter(score__gte=7.0, score__lt=8.0).count()),
            ('B (6.0-6.9)', all_grades.filter(score__gte=6.0, score__lt=7.0).count()),
            ('C+ (5.0-5.9)', all_grades.filter(score__gte=5.0, score__lt=6.0).count()),
            ('C (4.0-4.9)', all_grades.filter(score__gte=4.0, score__lt=5.0).count()),
            ('D+ (3.0-3.9)', all_grades.filter(score__gte=3.0, score__lt=4.0).count()),
            ('D (2.0-2.9)', all_grades.filter(score__gte=2.0, score__lt=3.0).count()),
            ('F (0-1.9)', all_grades.filter(score__lt=2.0).count()),
        ]
        context['grade_distribution'] = grade_ranges
        
        # Course statistics
        course_stats = []
        for course in Course.objects.filter(
            Q(teacher=teacher) | Q(assistant_teachers=teacher)
        ).distinct():
            course_grades = all_grades.filter(course=course)
            if course_grades.exists():
                course_stats.append({
                    'course': course,
                    'grade_count': course_grades.count(),
                    'average': course_grades.aggregate(avg=Avg('score'))['avg'],
                    'student_count': course.students.filter(profile__role='student').count(),
                })
        context['course_statistics'] = course_stats
        
        return context


class TeacherBulkGradeEntryView(TeacherRequiredMixin, FormView):
    """Bulk grade entry for multiple students"""
    form_class = TeacherBulkGradeForm
    template_name = 'dashboards/teacher/grade/bulk_entry.html'
    success_url = reverse_lazy('dashboards:teacher:grade_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            grades_data = json.loads(form.cleaned_data['grades_json'])
            created_count = 0
            
            for grade_data in grades_data:
                Grade.objects.create(
                    student_id=grade_data['student_id'],
                    course_id=grade_data['course_id'],
                    assignment_id=grade_data.get('assignment_id'),
                    grade_type=grade_data['grade_type'],
                    score=grade_data['score'],
                    max_score=grade_data['max_score'],
                    weight=grade_data.get('weight', 1.0),
                    date=grade_data['date'],
                    comment=grade_data.get('comment', ''),
                    created_by=self.request.user,
                )
                created_count += 1
            
            messages.success(
                self.request, 
                f'Đã nhập thành công {created_count} điểm!'
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            messages.error(self.request, f'Lỗi khi nhập điểm: {str(e)}')
            return self.form_invalid(form)
        
        return super().form_valid(form)


# =============================================================================
# STUDENT MANAGEMENT VIEWS
# =============================================================================

class TeacherStudentListView(TeacherRequiredMixin, ListView):
    """List all students taught by teacher"""
    model = User
    template_name = 'dashboards/teacher/student/list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def get_queryset(self):
        return User.objects.filter(
            Q(enrolled_courses__teacher=self.request.user) | Q(enrolled_courses__assistant_teachers=self.request.user),
            profile__role='student'
        ).select_related('profile').distinct().order_by('last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_students'] = self.get_queryset().count()
        context['courses'] = Course.objects.filter(
            Q(teacher=self.request.user) | Q(assistant_teachers=self.request.user)
        ).distinct()
        return context


class TeacherStudentDetailView(TeacherRequiredMixin, DetailView):
    """Student detail view for teacher"""
    model = User
    template_name = 'dashboards/teacher/student/detail.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        return User.objects.filter(
            Q(enrolled_courses__teacher=self.request.user) | Q(enrolled_courses__assistant_teachers=self.request.user),
            profile__role='student'
        ).select_related('profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        teacher = self.request.user
        
        # Get courses student is enrolled in with this teacher
        common_courses = Course.objects.filter(
            Q(teacher=teacher) | Q(assistant_teachers=teacher),
            students=student
        )
        
        # Get grades in these courses
        grades = Grade.objects.filter(
            student=student,
            course__in=common_courses
        ).select_related('course', 'assignment').order_by('-date')
        
        # Get submissions
        submissions = AssignmentSubmission.objects.filter(
            student=student,
            assignment__course__in=common_courses
        ).select_related('assignment', 'assignment__course').order_by('-submitted_at')
        
        context.update({
            'common_courses': common_courses,
            'grades': grades,
            'submissions': submissions,
            'average_grade': grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'total_grades': grades.count(),
            'total_submissions': submissions.count(),
        })
        
        return context


class TeacherStudentGradeView(TeacherRequiredMixin, DetailView):
    """View student grades across all courses"""
    model = User
    template_name = 'dashboards/teacher/student/grades.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        return User.objects.filter(
            Q(enrolled_courses__teacher=self.request.user) | Q(enrolled_courses__assistant_teachers=self.request.user),
            profile__role='student'
        ).select_related('profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        teacher = self.request.user
        
        # Get grades by course
        grades_by_course = {}
        for course in Course.objects.filter(
            Q(teacher=teacher) | Q(assistant_teachers=teacher),
            students=student
        ).distinct():
            course_grades = Grade.objects.filter(
                student=student,
                course=course
            ).order_by('-date')
            
            grades_by_course[course] = {
                'grades': course_grades,
                'average': course_grades.aggregate(avg=Avg('score'))['avg'] or 0,
                'count': course_grades.count(),
            }
        
        context['grades_by_course'] = grades_by_course
        
        # Overall statistics
        all_grades = Grade.objects.filter(
            student=student
        ).filter(
            Q(course__teacher=teacher) | Q(course__assistant_teachers=teacher)
        )
        
        context.update({
            'overall_average': all_grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'total_grades': all_grades.count(),
            'highest_grade': all_grades.aggregate(max=Max('score'))['max'] or 0,
            'lowest_grade': all_grades.aggregate(min=Min('score'))['min'] or 0,
        })
        
        return context 