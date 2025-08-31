"""
Assignment views for teachers
Views cho hệ thống bài tập (dành cho giáo viên)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.db import transaction
import os
import logging

from ..models.assignment import Assignment, AssignmentFile, AssignmentSubmission, AssignmentGrade
from ..models.study import Course
from ..forms.assignment_forms import (
    AssignmentForm, AssignmentFileUploadForm, AssignmentSubmissionForm,
    AssignmentGradeForm, AssignmentSearchForm, AssignmentSubmissionSearchForm
)

logger = logging.getLogger(__name__)


def is_teacher(user):
    """Kiểm tra user có phải giáo viên không"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if hasattr(user, 'profile') and user.profile:
        return user.profile.role == 'teacher'
    
    return False


@login_required
@user_passes_test(is_teacher)
def assignment_list(request):
    """Danh sách bài tập"""
    try:
        teacher = request.user
        
        # Lấy bài tập của giáo viên
        assignments = Assignment.objects.filter(
            Q(course__teacher=teacher) | Q(course__assistant_teachers=teacher)
        ).select_related('course').prefetch_related('submissions')
        
        # Form tìm kiếm
        search_form = AssignmentSearchForm(request.GET)
        if search_form.is_valid():
            search_query = search_form.cleaned_data.get('search_query')
            course_filter = search_form.cleaned_data.get('course_filter')
            status_filter = search_form.cleaned_data.get('status_filter')
            date_filter = search_form.cleaned_data.get('date_filter')
            
            # Tìm kiếm
            if search_query:
                assignments = assignments.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(course__name__icontains=search_query)
                )
            
            # Lọc theo môn học
            if course_filter:
                assignments = assignments.filter(course=course_filter)
            
            # Lọc theo trạng thái
            if status_filter:
                assignments = assignments.filter(status=status_filter)
            
            # Lọc theo thời gian
            if date_filter:
                now = timezone.now()
                if date_filter == 'today':
                    assignments = assignments.filter(created_at__date=now.date())
                elif date_filter == 'week':
                    from datetime import timedelta
                    week_ago = now - timedelta(days=7)
                    assignments = assignments.filter(created_at__gte=week_ago)
                elif date_filter == 'month':
                    from datetime import timedelta
                    month_ago = now - timedelta(days=30)
                    assignments = assignments.filter(created_at__gte=month_ago)
                elif date_filter == 'overdue':
                    assignments = assignments.filter(due_date__lt=now, status='active')
        
        # Sắp xếp
        sort_by = request.GET.get('sort', 'created_at')
        if sort_by == 'title':
            assignments = assignments.order_by('title')
        elif sort_by == 'course':
            assignments = assignments.order_by('course__name')
        elif sort_by == 'due_date':
            assignments = assignments.order_by('due_date')
        elif sort_by == 'status':
            assignments = assignments.order_by('status')
        else:
            assignments = assignments.order_by('-created_at')
        
        # Thống kê
        total_assignments = assignments.count()
        draft_assignments = assignments.filter(status='draft').count()
        active_assignments = assignments.filter(status='active').count()
        closed_assignments = assignments.filter(status='closed').count()
        
        # Phân trang
        paginator = Paginator(assignments, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'assignments': page_obj,
            'page_obj': page_obj,
            'search_form': search_form,
            'sort_by': sort_by,
            'total_assignments': total_assignments,
            'draft_assignments': draft_assignments,
            'active_assignments': active_assignments,
            'closed_assignments': closed_assignments,
        }
        
        return render(request, 'dashboards/teacher/assignment/list.html', context)
        
    except Exception as e:
        logger.error(f"Error in assignment list: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi tải danh sách bài tập.')
        return render(request, 'dashboards/teacher/assignment/list.html', {})


@login_required
@user_passes_test(is_teacher)
def assignment_create(request):
    """Tạo bài tập mới"""
    try:
        if request.method == 'POST':
            form = AssignmentForm(request.POST, request.FILES, user=request.user)
            if form.is_valid():
                with transaction.atomic():
                    # Tạo bài tập
                    assignment = form.save(commit=False)
                    assignment.created_by = request.user
                    
                    # Xử lý trạng thái từ button
                    if 'save_active' in request.POST:
                        assignment.status = 'active'
                        assignment.is_visible_to_students = True
                    
                    assignment.save()
                    
                    # Xử lý file upload
                    files = request.FILES.getlist('assignment_files')
                    for file in files:
                        assignment_file = AssignmentFile.objects.create(
                            assignment=assignment,
                            file=file,
                            uploaded_by=request.user,
                            is_submission_file=False
                        )
                    
                    messages.success(request, f'Đã tạo bài tập "{assignment.title}" thành công!')
                    return redirect('core:assignment_detail', pk=assignment.pk)
        else:
            form = AssignmentForm(user=request.user)
        
        context = {
            'form': form,
            'title': 'Tạo bài tập mới',
        }
        
        return render(request, 'dashboards/teacher/assignment/create.html', context)
        
    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi tạo bài tập.')
        return render(request, 'dashboards/teacher/assignment/create.html', {'form': form})


@login_required
@user_passes_test(is_teacher)
def assignment_detail(request, pk):
    """Chi tiết bài tập"""
    try:
        assignment = get_object_or_404(Assignment, pk=pk)
        
        # Kiểm tra quyền xem
        if not assignment.can_be_viewed_by(request.user):
            raise PermissionDenied("Bạn không có quyền xem bài tập này.")
        
        # Lấy danh sách bài nộp
        submissions = assignment.submissions.select_related('student').order_by('-submitted_at')
        
        # Thống kê
        total_submissions = submissions.count()
        graded_submissions = submissions.filter(status='graded').count()
        pending_submissions = submissions.filter(status__in=['submitted', 'late']).count()
        late_submissions = submissions.filter(status='late').count()
        
        # Lấy file đính kèm
        assignment_files = assignment.files.filter(is_submission_file=False)
        
        context = {
            'assignment': assignment,
            'submissions': submissions[:10],  # Chỉ hiển thị 10 bài nộp gần nhất
            'assignment_files': assignment_files,
            'total_submissions': total_submissions,
            'graded_submissions': graded_submissions,
            'pending_submissions': pending_submissions,
            'late_submissions': late_submissions,
        }
        
        return render(request, 'assignment/detail.html', context)
        
    except PermissionDenied:
        messages.error(request, 'Bạn không có quyền xem bài tập này.')
        return redirect('core:assignment_list')
    except Exception as e:
        logger.error(f"Error in assignment detail: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi tải chi tiết bài tập.')
        return redirect('core:assignment_list')


@login_required
@user_passes_test(is_teacher)
def assignment_submission_list(request, assignment_pk):
    """Danh sách bài nộp của một bài tập"""
    try:
        assignment = get_object_or_404(Assignment, pk=assignment_pk)
        
        # Kiểm tra quyền xem
        if not assignment.can_be_viewed_by(request.user):
            raise PermissionDenied("Bạn không có quyền xem bài tập này.")
        
        # Lấy danh sách bài nộp
        submissions = assignment.submissions.select_related('student').order_by('-submitted_at')
        
        # Form tìm kiếm
        search_form = AssignmentSubmissionSearchForm(request.GET)
        if search_form.is_valid():
            search_query = search_form.cleaned_data.get('search_query')
            status_filter = search_form.cleaned_data.get('status_filter')
            grade_filter = search_form.cleaned_data.get('grade_filter')
            
            # Tìm kiếm theo tên sinh viên
            if search_query:
                submissions = submissions.filter(
                    Q(student__first_name__icontains=search_query) |
                    Q(student__last_name__icontains=search_query) |
                    Q(student__username__icontains=search_query)
                )
            
            # Lọc theo trạng thái
            if status_filter:
                submissions = submissions.filter(status=status_filter)
            
            # Lọc theo tình trạng chấm điểm
            if grade_filter:
                if grade_filter == 'graded':
                    submissions = submissions.filter(status='graded')
                elif grade_filter == 'not_graded':
                    submissions = submissions.filter(status__in=['submitted', 'late'])
        
        # Thống kê
        total_submissions = submissions.count()
        graded_count = submissions.filter(status='graded').count()
        pending_count = submissions.filter(status__in=['submitted', 'late']).count()
        late_count = submissions.filter(status='late').count()
        
        # Phân trang
        paginator = Paginator(submissions, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'assignment': assignment,
            'submissions': page_obj,
            'page_obj': page_obj,
            'search_form': search_form,
            'total_submissions': total_submissions,
            'graded_count': graded_count,
            'pending_count': pending_count,
            'late_count': late_count,
        }
        
        return render(request, 'dashboards/teacher/assignment/submission_list.html', context)
        
    except PermissionDenied:
        messages.error(request, 'Bạn không có quyền xem bài tập này.')
        return redirect('core:assignment_list')
    except Exception as e:
        logger.error(f"Error in submission list: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi tải danh sách bài nộp.')
        return render(request, 'dashboards/teacher/assignment/submission_list.html', {})


@login_required
@user_passes_test(is_teacher)
def assignment_file_download(request, file_pk):
    """Tải file bài tập"""
    try:
        assignment_file = get_object_or_404(AssignmentFile, pk=file_pk)
        
        # Kiểm tra quyền tải file
        if not assignment_file.assignment.can_be_viewed_by(request.user):
            raise PermissionDenied("Bạn không có quyền tải file này.")
        
        # Kiểm tra file tồn tại
        if not os.path.exists(assignment_file.file.path):
            raise Http404("File không tồn tại.")
        
        # Tải file
        with open(assignment_file.file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{assignment_file.file_name}"'
            return response
            
    except PermissionDenied:
        messages.error(request, 'Bạn không có quyền tải file này.')
        return redirect('core:assignment_list')
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi tải file.')
        return redirect('core:assignment_list') 