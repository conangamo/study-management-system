"""
Core views
Views chính cho ứng dụng
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
import os
from django.db import transaction
import logging
from django.contrib.auth import authenticate, login, logout

from ..models.study import Course, Class
from ..models.assignment import Assignment
from ..models.user import UserProfile
from ..models.documents import Document, DocumentCategory, DocumentDownloadLog, DocumentComment
from ..forms import (
    DocumentUploadForm, DocumentEditForm, DocumentSearchForm, 
    DocumentCommentForm, DocumentCategoryForm
)
from ..admin_views import is_admin
from ..dashboards.admin.forms import AdminCourseForm, AdminClassForm, ClassSearchForm, BulkClassCreationForm
from ..models.study import CourseEnrollment


def can_upload_documents(user):
    """Helper function để kiểm tra user có thể upload tài liệu không"""
    if user.is_superuser:
        return True
    
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'teacher'
    except UserProfile.DoesNotExist:
        return False


def home(request):
    """Trang chủ"""
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated
    }
    return render(request, 'core/home.html', context)


def debug_view(request):
    """Debug view"""
    return JsonResponse({
        'message': 'Debug view working',
        'user': str(request.user),
        'is_authenticated': request.user.is_authenticated
    })


def simple_home(request):
    """Trang chủ đơn giản"""
    return render(request, 'core/simple_home.html')


def test_view(request):
    """Test view"""
    return JsonResponse({
        'message': 'Test view working',
        'user': str(request.user),
        'is_authenticated': request.user.is_authenticated
    })


@login_required
def test_auth_view(request):
    """Test view with login required"""
    return JsonResponse({
        'message': 'Auth test view working',
        'user': str(request.user),
        'is_authenticated': request.user.is_authenticated
    })


def test_student_dashboard(request):
    """Test student dashboard"""
    return render(request, 'core/test_student_dashboard.html')


def login_page(request):
    """Trang đăng nhập"""
    return render(request, 'core/auth/login.html')


def logout_view(request):
    """Đăng xuất"""
    logout(request)
    messages.success(request, 'Đã đăng xuất thành công!')
    return redirect('core:login_page')


@login_required
def profile_page(request):
    """Trang hồ sơ cá nhân"""
    context = {
        'user': request.user,
        'profile': getattr(request.user, 'profile', None)
    }
    return render(request, 'core/auth/profile.html', context)


def course_list(request):
    """API danh sách khóa học"""
    courses = Course.objects.all()  # Lấy tất cả courses thay vì chỉ active
    data = [{
        'id': course.id,
        'name': course.name,
        'code': course.code,
        'description': course.description,
        'credits': course.credits,
        'status': course.status
    } for course in courses]
    return JsonResponse({'courses': data})


def assignment_list(request):
    """API danh sách bài tập"""
    assignments = Assignment.objects.all()
    data = [{
        'id': assignment.id,
        'title': assignment.title,
        'description': assignment.description,
        'course': assignment.course.name if assignment.course else None,
        'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
        'max_score': float(assignment.max_score),
        'status': assignment.status
    } for assignment in assignments]
    return JsonResponse({'assignments': data})


# Document views
@login_required
def document_list(request):
    """Danh sách tài liệu"""
    documents = Document.objects.filter(
        status='active',
        visibility__in=['public', 'course_only']
    ).order_by('-created_at')
    categories = DocumentCategory.objects.all()
    
    # Search functionality
    search_form = DocumentSearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('q')
        category = search_form.cleaned_data.get('category')
        course = search_form.cleaned_data.get('course')
        
        if query:
            documents = documents.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if category:
            documents = documents.filter(category=category)
            
        if course:
            documents = documents.filter(course=course)
    
    # Pagination
    paginator = Paginator(documents, 12)  # 12 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'documents': page_obj,
        'categories': categories,
        'search_form': search_form,
        'can_upload': can_upload_documents(request.user)
    }
    return render(request, 'core/documents/list.html', context)


@login_required
@user_passes_test(can_upload_documents)
def document_upload(request):
    """Upload tài liệu"""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Tài liệu đã được upload thành công!')
            return redirect('core:document_detail', pk=document.pk)
    else:
        form = DocumentUploadForm()
    
    return render(request, 'core/documents/upload.html', {'form': form})


@login_required
def document_detail(request, pk):
    """Chi tiết tài liệu"""
    document = get_object_or_404(Document, pk=pk, status='active')
    
    # Log download activity
    if request.user != document.uploaded_by:
        DocumentDownloadLog.objects.create(
            document=document,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    # Get comments
    comments = DocumentComment.objects.filter(document=document).order_by('-created_at')
    
    # Comment form
    comment_form = DocumentCommentForm()
    if request.method == 'POST' and 'comment' in request.POST:
        comment_form = DocumentCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.document = document
            comment.user = request.user
            comment.save()
            messages.success(request, 'Bình luận đã được thêm!')
            return redirect('core:document_detail', pk=pk)
    
    # Related documents
    related_documents = Document.objects.filter(
        category=document.category,
        status='active'
    ).exclude(pk=pk)[:5]
    
    context = {
        'document': document,
        'comments': comments,
        'comment_form': comment_form,
        'related_documents': related_documents,
        'can_edit': request.user == document.uploaded_by or request.user.is_staff
    }
    return render(request, 'core/documents/detail.html', context)


@login_required
def document_download(request, pk):
    """Download tài liệu"""
    document = get_object_or_404(Document, pk=pk, status='active')
    
    # Log download
    DocumentDownloadLog.objects.create(
        document=document,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Update download count
    document.download_count += 1
    document.save()
    
    # Serve file
    file_path = document.file.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
            return response
    else:
        raise Http404("File not found")


@login_required
def document_edit(request, pk):
    """Chỉnh sửa tài liệu"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permissions
    if request.user != document.uploaded_by and not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = DocumentEditForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tài liệu đã được cập nhật!')
            return redirect('core:document_detail', pk=pk)
    else:
        form = DocumentEditForm(instance=document)
    
    return render(request, 'core/documents/edit.html', {
        'form': form,
        'document': document
    })


@login_required
def document_delete(request, pk):
    """Xóa tài liệu"""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permissions
    if request.user != document.uploaded_by and not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Tài liệu đã được xóa!')
        return redirect('core:document_list')
    
    return render(request, 'core/documents/delete_confirm.html', {
        'document': document
    })


@login_required
def document_categories(request):
    """Danh sách danh mục tài liệu"""
    categories = DocumentCategory.objects.annotate(
        document_count=Count('document')
    ).order_by('name')
    
    context = {
        'categories': categories
    }
    return render(request, 'core/documents/categories.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def document_statistics(request):
    """Thống kê tài liệu"""
    stats = {
        'total_documents': Document.objects.count(),
        'published_documents': Document.objects.filter(status='active').count(),
        'total_downloads': DocumentDownloadLog.objects.count(),
        'total_categories': DocumentCategory.objects.count(),
    }
    
    # Top downloaded documents
    top_documents = Document.objects.order_by('-download_count')[:10]
    
    # Recent uploads
    recent_documents = Document.objects.order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'top_documents': top_documents,
        'recent_documents': recent_documents
    }
    return render(request, 'core/documents/statistics.html', context)


@login_required
def document_my_uploads(request):
    """Tài liệu của tôi"""
    documents = Document.objects.filter(uploaded_by=request.user).order_by('-created_at')
    
    paginator = Paginator(documents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'documents': page_obj
    }
    return render(request, 'core/documents/my_uploads.html', context)


@login_required
def document_my_downloads(request):
    """Lịch sử download của tôi"""
    downloads = DocumentDownloadLog.objects.filter(user=request.user).order_by('-downloaded_at')
    
    paginator = Paginator(downloads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'downloads': page_obj
    }
    return render(request, 'core/documents/my_downloads.html', context)


# Admin Course Management Views
@login_required
@user_passes_test(is_admin)
def admin_course_list(request):
    """Admin: Danh sách khóa học"""
    courses = Course.objects.all().order_by('-created_at')
    
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'courses': page_obj
    }
    return render(request, 'core/admin/courses/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_course_create(request):
    """Admin: Tạo khóa học mới"""
    if request.method == 'POST':
        form = AdminCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Khóa học đã được tạo thành công!')
            return redirect('core:admin_course_list')
    else:
        form = AdminCourseForm()
    
    return render(request, 'core/admin/courses/create.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_course_edit(request, pk):
    """Admin: Chỉnh sửa khóa học"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        form = AdminCourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Khóa học đã được cập nhật!')
            return redirect('core:admin_course_list')
    else:
        form = AdminCourseForm(instance=course)
    
    return render(request, 'core/admin/courses/edit.html', {
        'form': form,
        'course': course
    })


@login_required
@user_passes_test(is_admin)
def admin_course_delete(request, pk):
    """Admin: Xóa khóa học"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Khóa học đã được xóa!')
        return redirect('core:admin_course_list')
    
    return render(request, 'core/admin/courses/delete_confirm.html', {
        'course': course
    })


# Admin Class Management Views
@login_required
@user_passes_test(is_admin)
def admin_class_list(request):
    """Admin: Danh sách lớp học"""
    classes = Class.objects.all().order_by('-created_at')
    
    # Search functionality
    search_form = ClassSearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        course = search_form.cleaned_data.get('course')
        
        if query:
            classes = classes.filter(
                Q(name__icontains=query) | 
                Q(code__icontains=query)
            )
        
        if course:
            classes = classes.filter(course=course)
    
    paginator = Paginator(classes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'classes': page_obj,
        'search_form': search_form
    }
    return render(request, 'core/admin/classes/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_class_create(request):
    """Admin: Tạo lớp học mới"""
    if request.method == 'POST':
        form = AdminClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lớp học đã được tạo thành công!')
            return redirect('core:admin_class_list')
    else:
        form = AdminClassForm()
    
    return render(request, 'core/admin/classes/create.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_class_edit(request, pk):
    """Admin: Chỉnh sửa lớp học"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        form = AdminClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lớp học đã được cập nhật!')
            return redirect('core:admin_class_list')
    else:
        form = AdminClassForm(instance=class_obj)
    
    return render(request, 'core/admin/classes/edit.html', {
        'form': form,
        'class': class_obj
    })


@login_required
@user_passes_test(is_admin)
def admin_class_delete(request, pk):
    """Admin: Xóa lớp học"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    if request.method == 'POST':
        class_obj.delete()
        messages.success(request, 'Lớp học đã được xóa!')
        return redirect('core:admin_class_list')
    
    return render(request, 'core/admin/classes/delete_confirm.html', {
        'class': class_obj
    })


@login_required
@user_passes_test(is_admin)
def admin_class_detail(request, pk):
    """Admin: Chi tiết lớp học"""
    class_obj = get_object_or_404(Class, pk=pk)
    
    context = {
        'class': class_obj,
        'students': class_obj.students.all(),
        'student_count': class_obj.students.count()
    }
    return render(request, 'core/admin/classes/detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_bulk_create_classes(request):
    """Admin: Tạo lớp học hàng loạt"""
    if request.method == 'POST':
        form = BulkClassCreationForm(request.POST)
        if form.is_valid():
            # Logic tạo lớp hàng loạt
            course = form.cleaned_data['course']
            prefix = form.cleaned_data['class_prefix']
            count = form.cleaned_data['class_count']
            
            created_classes = []
            for i in range(1, count + 1):
                class_name = f"{prefix}{i:02d}"
                class_code = f"{course.code}_{class_name}"
                
                class_obj, created = Class.objects.get_or_create(
                    code=class_code,
                    defaults={
                        'name': class_name,
                        'course': course,
                        'max_students': form.cleaned_data.get('max_students', 30)
                    }
                )
                
                if created:
                    created_classes.append(class_obj)
            
            messages.success(request, f'Đã tạo {len(created_classes)} lớp học mới!')
            return redirect('core:admin_class_list')
    else:
        form = BulkClassCreationForm()
    
    return render(request, 'core/admin/classes/bulk_create.html', {'form': form})


# Student Course Management Views
@login_required
def student_course_list(request):
    """Danh sách khóa học cho sinh viên"""
    courses = Course.objects.filter(status='active').order_by('name')
    
    # Thêm enrolled_count cho mỗi course
    for course in courses:
        course.enrolled_count = course.enrolled_student_count
    
    # Lấy danh sách ID các môn đã đăng ký
    enrolled_course_ids = []
    if hasattr(request.user, 'profile') and request.user.profile.is_student:
        enrolled_course_ids = list(
            CourseEnrollment.objects.filter(
                student=request.user,
                status__in=['enrolled', 'completed']
            ).values_list('course_id', flat=True)
        )
    
    context = {
        'courses': courses,
        'enrolled_courses': enrolled_course_ids
    }
    return render(request, 'core/student/courses/list.html', context)


@login_required
def student_course_register(request, course_id):
    """Đăng ký khóa học"""
    print(f"DEBUG: Starting registration - User: {request.user.id}, Course: {course_id}, Method: {request.method}")
    
    course = get_object_or_404(Course, id=course_id)
    print(f"DEBUG: Found course: {course.name} (ID: {course.id})")
    
    # Kiểm tra user có phải student không
    if not hasattr(request.user, 'profile') or not request.user.profile.is_student:
        print(f"DEBUG: User is not student - hasattr: {hasattr(request.user, 'profile')}")
        if hasattr(request.user, 'profile'):
            print(f"DEBUG: User role: {request.user.profile.role}")
        messages.error(request, 'Chỉ sinh viên mới có thể đăng ký môn học.')
        return redirect('core:student_course_list')
    
    print(f"DEBUG: User is student - Role: {request.user.profile.role}")
    
    # Kiểm tra course có thể đăng ký không
    if course.status not in ['upcoming', 'active']:
        print(f"DEBUG: Course status not valid: {course.status}")
        messages.error(request, 'Không thể đăng ký môn học này.')
        return redirect('core:student_course_list')
    
    print(f"DEBUG: Course status OK: {course.status}")
    
    # Kiểm tra đã đăng ký chưa
    existing_enrollment = CourseEnrollment.objects.filter(
        student=request.user, 
        course=course
    ).first()  # Tìm bất kỳ enrollment nào, không phân biệt status
    
    print(f"DEBUG: Existing enrollment check - Found: {existing_enrollment is not None}")
    if existing_enrollment:
        print(f"DEBUG: Existing enrollment status: {existing_enrollment.status}")
    
    if existing_enrollment:
        if existing_enrollment.status in ['enrolled', 'completed']:
            messages.info(request, f'Bạn đã đăng ký môn học {course.name} rồi.')
            return redirect('core:student_course_list')
        elif existing_enrollment.status == 'dropped':
            # Nếu đã hủy đăng ký trước đó, cho phép đăng ký lại bằng cách cập nhật status
            print(f"DEBUG: Re-enrolling dropped course")
            existing_enrollment.status = 'enrolled'
            existing_enrollment.enrolled_at = timezone.now()
            existing_enrollment.dropped_at = None
            existing_enrollment.save()
            
            messages.success(request, f'Đã đăng ký lại khóa học {course.name} thành công!')
            print(f"DEBUG: Re-enrolled course - Student: {request.user.id}, Course: {course.id}")
            
            # Render trực tiếp trang course list với updated data
            courses = Course.objects.filter(status='active').order_by('name')
            
            # Thêm enrolled_count cho mỗi course
            for course in courses:
                course.enrolled_count = course.enrolled_student_count
                
            enrolled_course_ids = list(
                CourseEnrollment.objects.filter(
                    student=request.user,
                    status__in=['enrolled', 'completed']
                ).values_list('course_id', flat=True)
            )
            
            context = {
                'courses': courses,
                'enrolled_courses': enrolled_course_ids
            }
            return render(request, 'core/student/courses/list.html', context)
    
    # Kiểm tra môn học có đầy không
    if course.is_full:
        print(f"DEBUG: Course is full")
        messages.error(request, f'Môn học {course.name} đã đầy.')
        return redirect('core:student_course_list')
    
    print(f"DEBUG: Course not full, proceeding to create enrollment")
    
    # Tạo enrollment
    try:
        enrollment = CourseEnrollment.objects.create(
            student=request.user,
            course=course,
            status='enrolled'
        )
        messages.success(request, f'Đã đăng ký khóa học {course.name} thành công!')
        print(f"DEBUG: Created enrollment - Student: {request.user.id}, Course: {course.id}, Status: enrolled")
        print(f"DEBUG: Enrollment ID: {enrollment.id}")
        print(f"DEBUG: Redirecting to core:student_course_list")
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra khi đăng ký: {str(e)}')
        print(f"DEBUG: Error occurred: {str(e)}")
        print(f"DEBUG: Exception type: {type(e).__name__}")
    
    print(f"DEBUG: About to redirect to core:student_course_list")
    
    # Thay vì redirect, render trực tiếp trang course list
    courses = Course.objects.filter(status='active').order_by('name')
    
    # Thêm enrolled_count cho mỗi course
    for course in courses:
        course.enrolled_count = course.enrolled_student_count
    
    # Lấy danh sách ID các môn đã đăng ký (cập nhật sau khi đăng ký)
    enrolled_course_ids = []
    if hasattr(request.user, 'profile') and request.user.profile.is_student:
        enrolled_course_ids = list(
            CourseEnrollment.objects.filter(
                student=request.user,
                status__in=['enrolled', 'completed']
            ).values_list('course_id', flat=True)
        )
    
    context = {
        'courses': courses,
        'enrolled_courses': enrolled_course_ids
    }
    return render(request, 'core/student/courses/list.html', context)


@login_required
def student_course_unregister(request, course_id):
    """Hủy đăng ký khóa học"""
    course = get_object_or_404(Course, id=course_id)
    
    # Kiểm tra user có phải student không
    if not hasattr(request.user, 'profile') or not request.user.profile.is_student:
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('core:student_course_list')
    
    # Tìm enrollment
    try:
        enrollment = CourseEnrollment.objects.get(
            student=request.user,
            course=course,
            status='enrolled'
        )
        
        # Hủy đăng ký (đổi status thành dropped)
        enrollment.status = 'dropped'
        enrollment.dropped_at = timezone.now()
        enrollment.save()
        
        messages.success(request, f'Đã hủy đăng ký khóa học {course.name}!')
        
    except CourseEnrollment.DoesNotExist:
        messages.error(request, f'Bạn chưa đăng ký môn học {course.name}.')
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra khi hủy đăng ký: {str(e)}')
    
    return redirect('core:student_enrolled_courses')


@login_required
def student_enrolled_courses(request):
    """Khóa học đã đăng ký"""
    print(f"DEBUG: student_enrolled_courses - User: {request.user.id}")
    
    # Kiểm tra user có phải student không
    if not hasattr(request.user, 'profile') or not request.user.profile.is_student:
        print(f"DEBUG: User is not student")
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('core:home')
    
    print(f"DEBUG: User is student - Role: {request.user.profile.role}")
    
    # Debug: Kiểm tra tất cả enrollments của user này
    all_enrollments = CourseEnrollment.objects.filter(student=request.user)
    print(f"DEBUG: All enrollments for user {request.user.id}: {all_enrollments.count()}")
    for enrollment in all_enrollments:
        print(f"DEBUG: All enrollment - Course: {enrollment.course.name}, Status: {enrollment.status}, Date: {enrollment.enrolled_at}")
    
    # Lấy danh sách môn học đã đăng ký
    enrolled_courses = CourseEnrollment.objects.filter(
        student=request.user,
        status__in=['enrolled', 'completed']
    ).select_related('course', 'course__teacher').order_by('-enrolled_at')
    
    print(f"DEBUG: Enrolled courses query - Count: {enrolled_courses.count()}")
    for enrollment in enrolled_courses:
        print(f"DEBUG: Enrollment - Course: {enrollment.course.name}, Status: {enrollment.status}, Date: {enrollment.enrolled_at}")
    
    # Tính toán statistics
    total_courses = enrolled_courses.count()
    total_credits = sum(enrollment.course.credits for enrollment in enrolled_courses)
    
    print(f"DEBUG: Statistics - Total courses: {total_courses}, Total credits: {total_credits}")
    
    context = {
        'enrollments': enrolled_courses,
        'courses': [enrollment.course for enrollment in enrolled_courses],  # Để tương thích với template cũ
        'enrolled_courses': [enrollment.course for enrollment in enrolled_courses],  # Thêm cho template
        'total_courses': total_courses,
        'total_credits': total_credits,
    }
    return render(request, 'core/student/courses/enrolled.html', context)


def test_redirect_view(request):
    """Test redirect view"""
    messages.success(request, 'Test redirect thành công!')
    return redirect('/course/') 