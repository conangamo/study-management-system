"""
Student Dashboard Views
- Course viewing and enrollment
- Assignment tracking and submissions
- Grade monitoring and statistics
- Personal notes management
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.db.models import Avg, Count, Q, Max, Min
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from datetime import timedelta
from django.views import View

from core.models.study import Course, CourseEnrollment, Grade, Note
from core.models.assignment import Assignment, AssignmentSubmission
from core.models.academic import AcademicYear


class StudentRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure user is logged in and has student role
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has student profile
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Tài khoản chưa được thiết lập profile.')
            return redirect('core:profile')
        
        if not request.user.profile.is_student:
            messages.error(request, 'Bạn không có quyền truy cập vào trang này.')
            return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)


class StudentDashboardView(StudentRequiredMixin, TemplateView):
    """Student Dashboard main view"""
    template_name = 'dashboards/student/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get student's enrolled courses
        enrolled_courses = CourseEnrollment.objects.filter(
            student=user, status='enrolled'
        ).select_related('course', 'course__teacher')
        
        # Get upcoming assignments
        upcoming_assignments = Assignment.objects.filter(
            course__enrollments__student=user,
            course__enrollments__status='enrolled',
            due_date__gte=timezone.now()
        ).order_by('due_date')[:5]
        
        # Get recent grades
        recent_grades = Grade.objects.filter(
            student=user
        ).select_related('course', 'assignment').order_by('-created_at')[:5]
        
        # Calculate statistics
        total_courses = enrolled_courses.count()
        pending_assignments = Assignment.objects.filter(
            course__enrollments__student=user,
            course__enrollments__status='enrolled',
            due_date__gte=timezone.now()
        ).exclude(
            submissions__student=user
        ).count()
        
        avg_grade = Grade.objects.filter(student=user).aggregate(
            avg_score=Avg('score')
        )['avg_score'] or 0
        
        total_notes = Note.objects.filter(user=user).count()
        
        context.update({
            'student': user,
            'student_profile': user.profile,
            'enrolled_courses': enrolled_courses,
            'upcoming_assignments': upcoming_assignments,
            'recent_grades': recent_grades,
            'stats': {
                'total_courses': total_courses,
                'pending_assignments': pending_assignments,
                'average_grade': round(avg_grade, 2) if avg_grade else 0,
                'total_notes': total_notes,
            }
        })
        
        return context


class StudentCourseListView(StudentRequiredMixin, ListView):
    """List all courses the student is enrolled in"""
    template_name = 'dashboards/student/course/list.html'
    context_object_name = 'enrollments'
    paginate_by = 10
    
    def get_queryset(self):
        return CourseEnrollment.objects.filter(
            student=self.request.user,
            status='enrolled'
        ).select_related('course', 'course__teacher').order_by('-enrolled_at')


class StudentCourseDetailView(StudentRequiredMixin, DetailView):
    """Course detail view for students"""
    template_name = 'dashboards/student/course/detail.html'
    context_object_name = 'course'
    
    def get_object(self):
        course_id = self.kwargs['pk']
        # Ensure student is enrolled in this course
        enrollment = get_object_or_404(
            CourseEnrollment,
            course_id=course_id,
            student=self.request.user,
            status='enrolled'
        )
        return enrollment.course
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        student = self.request.user
        
        # Get course assignments
        assignments = Assignment.objects.filter(course=course).order_by('-created_at')
        
        # Get student's grades for this course
        grades = Grade.objects.filter(
            student=student,
            course=course
        ).select_related('assignment').order_by('-created_at')
        
        # Get course statistics
        avg_grade = grades.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        
        context.update({
            'assignments': assignments,
            'grades': grades,
            'course_avg_grade': round(avg_grade, 2) if avg_grade else 0,
        })
        
        return context


class StudentAssignmentListView(StudentRequiredMixin, ListView):
    """List enrolled courses with assignment statistics"""
    template_name = 'dashboards/student/assignment/list.html'
    context_object_name = 'enrolled_courses'
    paginate_by = 15
    
    def get_queryset(self):
        """Get courses that student is enrolled in"""
        return Course.objects.filter(
            enrollments__student=self.request.user,
            enrollments__status='enrolled'
        ).select_related('teacher').prefetch_related('assignments').order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        
        # Add assignment statistics for each course
        for course in context['enrolled_courses']:
            # Get assignments for this course that are visible to students
            course_assignments = course.assignments.filter(
                is_visible_to_students=True,
                status='active'
            )
            
            # Calculate statistics
            total_assignments = course_assignments.count()
            submitted_assignments = AssignmentSubmission.objects.filter(
                assignment__in=course_assignments,
                student=student
            ).count()
            
            overdue_assignments = course_assignments.filter(
                due_date__lt=timezone.now()
            ).exclude(
                submissions__student=student
            ).count()
            
            # Add to course object
            course.total_assignments = total_assignments
            course.submitted_assignments = submitted_assignments
            course.pending_assignments = total_assignments - submitted_assignments
            course.overdue_assignments = overdue_assignments
        
        return context


class StudentAssignmentDetailView(StudentRequiredMixin, DetailView):
    """Assignment detail view for students with submission functionality"""
    template_name = 'dashboards/student/assignment/detail.html'
    context_object_name = 'assignment'
    
    def get_object(self):
        assignment_id = self.kwargs['pk']
        # Ensure student has access to this assignment
        return get_object_or_404(
            Assignment,
            id=assignment_id,
            course__enrollments__student=self.request.user,
            course__enrollments__status='enrolled',
            is_visible_to_students=True,
            status='active'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.object
        student = self.request.user
        
        # Get student's submission
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        # Get grade for this assignment
        grade = Grade.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        # Determine submission status
        is_overdue = assignment.due_date < timezone.now()
        can_submit = not is_overdue or assignment.allow_late_submission
        
        # Status display
        if submission:
            if grade and grade.score is not None:
                status_display = 'Đã chấm điểm'
                status_class = 'success'
            elif submission.status == 'late':
                status_display = 'Đã nộp (Trễ hạn)'
                status_class = 'warning'
            else:
                status_display = 'Đã nộp'
                status_class = 'info'
        else:
            if is_overdue:
                status_display = 'Quá hạn'
                status_class = 'danger'
            else:
                status_display = 'Chưa nộp'
                status_class = 'secondary'
        
        context.update({
            'submission': submission,
            'grade': grade,
            'is_submitted': submission is not None,
            'is_overdue': is_overdue,
            'can_submit': can_submit,
            'can_edit': submission is not None and can_submit,
            'status_display': status_display,
            'status_class': status_class,
            'time_remaining': assignment.due_date - timezone.now() if assignment.due_date > timezone.now() else None,
            'allowed_file_types': assignment.allowed_file_types,
            'max_file_size_mb': assignment.max_file_size,
        })
        
        return context


class StudentGradeListView(StudentRequiredMixin, ListView):
    """List all grades for the student"""
    template_name = 'dashboards/student/grade/list.html'
    context_object_name = 'grades'
    paginate_by = 20
    
    def get_queryset(self):
        return Grade.objects.filter(
            student=self.request.user
        ).select_related('course', 'assignment').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        
        # Calculate grade statistics
        grades = Grade.objects.filter(student=student)
        
        stats = {
            'total_grades': grades.count(),
            'average_score': grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'highest_score': grades.aggregate(max_score=Max('score'))['max_score'] or 0,
            'lowest_score': grades.aggregate(min_score=Min('score'))['min_score'] or 0,
        }
        
        # Grade distribution by course
        course_grades = grades.values('course__name').annotate(
            avg_score=Avg('score'),
            count=Count('id')
        ).order_by('-avg_score')
        
        context.update({
            'stats': stats,
            'course_grades': course_grades,
        })
        
        return context


class StudentNoteListView(StudentRequiredMixin, ListView):
    """List student's personal notes"""
    template_name = 'dashboards/student/note/list.html'
    context_object_name = 'notes'
    paginate_by = 15
    
    def get_queryset(self):
        return Note.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class StudentNoteCreateView(StudentRequiredMixin, CreateView):
    """Create a new note"""
    model = Note
    template_name = 'dashboards/student/note/create.html'
    fields = ['title', 'content', 'tags']
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Ghi chú đã được tạo thành công!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:dashboards:student:notes')


class StudentNoteDetailView(StudentRequiredMixin, DetailView):
    """Note detail view"""
    template_name = 'dashboards/student/note/detail.html'
    context_object_name = 'note'
    
    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)


class StudentNoteUpdateView(StudentRequiredMixin, UpdateView):
    """Update a note"""
    model = Note
    template_name = 'dashboards/student/note/edit.html'
    fields = ['title', 'content', 'tags']
    
    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Ghi chú đã được cập nhật!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:dashboards:student:note_detail', kwargs={'pk': self.object.pk}) 


class StudentCourseCatalogView(StudentRequiredMixin, ListView):
    """Danh sách các môn học mà sinh viên có thể đăng ký"""
    template_name = 'dashboards/student/course/catalog.html'
    context_object_name = 'courses'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        q = self.request.GET.get('q')
        year = user.profile.academic_year
        qs = Course.objects.select_related('teacher', 'academic_year').filter(
            Q(status__in=['upcoming', 'active']) &
            (Q(academic_year=year) | Q(academic_year__isnull=True))
        )
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(teacher__first_name__icontains=q) | Q(teacher__last_name__icontains=q))
        return qs.order_by('name').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        return context


class StudentCourseEnrollView(StudentRequiredMixin, View):
    """Xử lý đăng ký môn học từ dashboard sinh viên"""
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        if course.status != 'upcoming':
            messages.error(request, 'Không thể đăng ký môn học này.')
            return redirect('dashboards:student:courses')
        if course.is_full:
            messages.error(request, 'Môn học đã đầy.')
            return redirect('dashboards:student:courses')
        if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
            messages.info(request, 'Bạn đã đăng ký môn học này.')
            return redirect('dashboards:student:courses')
        CourseEnrollment.objects.create(student=request.user, course=course)
        messages.success(request, 'Đăng ký môn học thành công!')
        return redirect('dashboards:student:courses') 


class StudentCourseAssignmentListView(StudentRequiredMixin, ListView):
    """List assignments for a specific course"""
    template_name = 'dashboards/student/assignment/course_assignments.html'
    context_object_name = 'assignments'
    paginate_by = 20
    
    def get_course(self):
        """Get the course object"""
        if not hasattr(self, '_course'):
            course_id = self.kwargs['course_id']
            self._course = get_object_or_404(
                Course,
                id=course_id,
                enrollments__student=self.request.user,
                enrollments__status='enrolled'
            )
        return self._course
    
    def get_queryset(self):
        """Get assignments for the specific course"""
        course = self.get_course()
        return Assignment.objects.filter(
            course=course,
            is_visible_to_students=True,
            status='active'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        course = self.get_course()
        
        # Add submission status for each assignment
        for assignment in context['assignments']:
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=student
            ).first()
            
            assignment.submission = submission
            assignment.is_submitted = submission is not None
            assignment.is_deadline_passed = assignment.due_date < timezone.now()
            
            # Determine status
            if submission:
                if submission.status == 'graded':
                    assignment.status_display = 'Đã chấm điểm'
                    assignment.status_class = 'success'
                elif assignment.is_deadline_passed:
                    assignment.status_display = 'Đã nộp (Trễ hạn)'
                    assignment.status_class = 'warning'
                else:
                    assignment.status_display = 'Đã nộp'
                    assignment.status_class = 'info'
            else:
                if assignment.is_deadline_passed:
                    assignment.status_display = 'Quá hạn'
                    assignment.status_class = 'danger'
                else:
                    assignment.status_display = 'Chưa nộp'
                    assignment.status_class = 'secondary'
        
        # Course statistics
        course_assignments = Assignment.objects.filter(
            course=course,
            is_visible_to_students=True,
            status='active'
        )
        
        total_assignments = course_assignments.count()
        submitted_count = AssignmentSubmission.objects.filter(
            assignment__in=course_assignments,
            student=student
        ).count()
        
        context.update({
            'course': course,
            'total_assignments': total_assignments,
            'submitted_assignments': submitted_count,
            'pending_assignments': total_assignments - submitted_count,
        })
        
        return context 


class StudentAssignmentSubmitView(StudentRequiredMixin, View):
    """Handle assignment submission and file uploads"""
    
    def get_assignment(self):
        """Get assignment object with permission check"""
        assignment_id = self.kwargs['pk']
        return get_object_or_404(
            Assignment,
            id=assignment_id,
            course__enrollments__student=self.request.user,
            course__enrollments__status='enrolled',
            is_visible_to_students=True,
            status='active'
        )
    
    def post(self, request, *args, **kwargs):
        assignment = self.get_assignment()
        student = request.user
        
        # Check if submission is allowed
        is_overdue = assignment.due_date < timezone.now()
        if is_overdue and not assignment.allow_late_submission:
            messages.error(request, 'Đã quá hạn nộp bài và không được phép nộp muộn.')
            return redirect('dashboards:student:assignment_detail', pk=assignment.pk)
        
        # Get uploaded file
        uploaded_file = request.FILES.get('assignment_file')
        if not uploaded_file:
            messages.error(request, 'Vui lòng chọn file để nộp bài.')
            return redirect('dashboards:student:assignment_detail', pk=assignment.pk)
        
        # Validate file type
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in assignment.allowed_file_types:
            allowed_types = ', '.join(assignment.allowed_file_types).upper()
            messages.error(request, f'Loại file không được hỗ trợ. Chỉ chấp nhận: {allowed_types}')
            return redirect('dashboards:student:assignment_detail', pk=assignment.pk)
        
        # Validate file size (convert MB to bytes)
        max_size_bytes = assignment.max_file_size * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            messages.error(request, f'File quá lớn. Kích thước tối đa: {assignment.max_file_size}MB')
            return redirect('dashboards:student:assignment_detail', pk=assignment.pk)
        
        # Get or create submission
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=student,
            defaults={
                'status': 'late' if is_overdue else 'submitted',
                'comments': request.POST.get('comments', ''),
            }
        )
        
        # Update submission if it already exists
        if not created:
            submission.status = 'late' if is_overdue else 'submitted'
            submission.comments = request.POST.get('comments', '')
            submission.submitted_at = timezone.now()
        
        # Handle file upload
        # If updating, we need to replace the old file
        if hasattr(submission, 'files') and submission.files.exists():
            # Delete old files
            for old_file in submission.files.all():
                if old_file.file:
                    old_file.file.delete()
                old_file.delete()
        
        # Create new file record
        from core.models.assignment import AssignmentFile
        AssignmentFile.objects.create(
            assignment=assignment,
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_type=f'.{file_extension}',
            file_size=uploaded_file.size,
            uploaded_by=student,
            is_submission_file=True,
            description=f'Bài nộp của {student.get_full_name()}'
        )
        
        submission.save()
        
        # Success message
        action = 'cập nhật' if not created else 'nộp'
        status_msg = ' (nộp muộn)' if is_overdue else ''
        messages.success(request, f'Đã {action} bài tập thành công{status_msg}!')
        
        return redirect('dashboards:student:assignment_detail', pk=assignment.pk) 