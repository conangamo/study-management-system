"""
Study Management API Views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from core.models import (
    Course, CourseEnrollment, Assignment, AssignmentSubmission,
    Grade, Tag, Note
)
from ..serializers import (
    CourseSerializer, CourseEnrollmentSerializer, AssignmentSerializer,
    AssignmentSubmissionSerializer, GradeSerializer, TagSerializer,
    NoteSerializer, NoteCreateSerializer, BulkEnrollmentSerializer,
    CourseAnalyticsSerializer, StudentPerformanceSerializer
)
from ..permissions import (
    IsTeacherOrAdmin, IsAdminOnly, IsCourseTeacherOrAdmin,
    IsEnrolledStudentOrTeacherOrAdmin, CanManageAssignment,
    CanSubmitAssignment, CanGradeAssignment, IsOwnerOrReadOnly
)


# =============================================================================
# COURSE VIEWS
# =============================================================================

class CourseListCreateView(generics.ListCreateAPIView):
    """
    List courses hoặc tạo course mới
    """
    queryset = Course.objects.select_related('teacher').prefetch_related('students').all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'semester', 'academic_year', 'teacher']
    search_fields = ['name', 'code', 'teacher__first_name', 'teacher__last_name']
    ordering_fields = ['name', 'code', 'created_at', 'start_date']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            # Chỉ admin được phép tạo course
            return [IsAdminOnly()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admin xem tất cả
        if hasattr(user, 'profile') and user.profile.role == 'admin':
            return queryset
        
        # Teacher chỉ xem course mình phụ trách hoặc hỗ trợ
        if hasattr(user, 'profile') and user.profile.role == 'teacher':
            return queryset.filter(Q(teacher=user) | Q(assistant_teachers=user)).distinct()
        
        # Student: thấy các môn đã đăng ký hoặc phù hợp với năm học của họ, hoặc môn tự chọn (không gắn năm học)
        if hasattr(user, 'profile') and user.profile.role == 'student':
            return queryset.filter(
                Q(students=user) |
                Q(academic_year=user.profile.academic_year) |
                Q(academic_year__isnull=True)
            ).distinct()
        
        return queryset.none()


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa course
    """
    queryset = Course.objects.select_related('teacher').prefetch_related('students').all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated, IsEnrolledStudentOrTeacherOrAdmin]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Chỉ admin được cập nhật/xóa
            return [IsAdminOnly()]
        return [permissions.IsAuthenticated(), IsEnrolledStudentOrTeacherOrAdmin()]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_course(request, pk):
    """
    Sinh viên đăng ký môn học
    """
    if request.user.profile.role != 'student':
        return Response({
            'error': 'Chỉ sinh viên mới có thể đăng ký môn học.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        course = Course.objects.get(pk=pk)
        
        # Kiểm tra course có thể đăng ký không
        if course.status != 'upcoming':
            return Response({
                'error': 'Không thể đăng ký môn học này.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if course.is_full:
            return Response({
                'error': 'Môn học đã đầy.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra đã đăng ký chưa
        if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
            return Response({
                'error': 'Bạn đã đăng ký môn học này rồi.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo enrollment
        enrollment = CourseEnrollment.objects.create(
            student=request.user,
            course=course
        )
        
        serializer = CourseEnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Course.DoesNotExist:
        return Response({
            'error': 'Không tìm thấy môn học.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def drop_course(request, pk):
    """
    Sinh viên rút môn học
    """
    try:
        enrollment = CourseEnrollment.objects.get(
            course_id=pk, 
            student=request.user
        )
        
        if enrollment.status != 'enrolled':
            return Response({
                'error': 'Không thể rút môn học này.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        enrollment.drop_course()
        
        return Response({
            'message': 'Rút môn học thành công.'
        }, status=status.HTTP_200_OK)
        
    except CourseEnrollment.DoesNotExist:
        return Response({
            'error': 'Bạn chưa đăng ký môn học này.'
        }, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# ASSIGNMENT VIEWS
# =============================================================================

class AssignmentListCreateView(generics.ListCreateAPIView):
    """
    List assignments hoặc tạo assignment mới
    """
    queryset = Assignment.objects.select_related('course', 'created_by').all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'assignment_type', 'priority', 'course']
    search_fields = ['title', 'description', 'course__name']
    ordering_fields = ['title', 'due_date', 'created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admin xem tất cả
        if user.profile.role == 'admin':
            return queryset
        
        # Teacher chỉ xem assignment của course mình dạy
        elif user.profile.role == 'teacher':
            return queryset.filter(course__teacher=user)
        
        # Student chỉ xem assignment của course đã đăng ký
        elif user.profile.role == 'student':
            return queryset.filter(course__students=user)
        
        return queryset.none()


class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa assignment
    """
    queryset = Assignment.objects.select_related('course', 'created_by').all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageAssignment]


@api_view(['POST'])
@permission_classes([IsTeacherOrAdmin])
def publish_assignment(request, pk):
    """
    Công bố assignment
    """
    try:
        assignment = Assignment.objects.get(pk=pk)
        
        # Kiểm tra quyền
        if (request.user.profile.role == 'teacher' and 
            assignment.course.teacher != request.user):
            return Response({
                'error': 'Không có quyền.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if assignment.status != 'draft':
            return Response({
                'error': 'Assignment này đã được công bố.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        assignment.publish()
        
        return Response({
            'message': 'Công bố assignment thành công.'
        }, status=status.HTTP_200_OK)
        
    except Assignment.DoesNotExist:
        return Response({
            'error': 'Không tìm thấy assignment.'
        }, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# SUBMISSION VIEWS
# =============================================================================

class AssignmentSubmissionListCreateView(generics.ListCreateAPIView):
    """
    List submissions hoặc tạo submission mới
    """
    queryset = AssignmentSubmission.objects.select_related('assignment', 'student').all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'assignment', 'is_late']
    ordering_fields = ['submitted_at', 'score']
    ordering = ['-submitted_at']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [CanSubmitAssignment()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admin và Teacher xem submission của course mình dạy
        if user.profile.role in ['admin', 'teacher']:
            if user.profile.role == 'teacher':
                return queryset.filter(assignment__course__teacher=user)
            return queryset
        
        # Student chỉ xem submission của mình
        elif user.profile.role == 'student':
            return queryset.filter(student=user)
        
        return queryset.none()


class AssignmentSubmissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa submission
    """
    queryset = AssignmentSubmission.objects.select_related('assignment', 'student').all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, CanSubmitAssignment]


# =============================================================================
# GRADE VIEWS
# =============================================================================

class GradeListCreateView(generics.ListCreateAPIView):
    """
    List grades hoặc tạo grade mới
    """
    queryset = Grade.objects.select_related(
        'student', 'course', 'assignment', 'created_by'
    ).all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['grade_type', 'course', 'student', 'is_final']
    ordering_fields = ['date', 'score']
    ordering = ['-date']
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [CanGradeAssignment()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Admin xem tất cả
        if user.profile.role == 'admin':
            return queryset
        
        # Teacher xem grade của course mình dạy
        elif user.profile.role == 'teacher':
            return queryset.filter(course__teacher=user)
        
        # Student chỉ xem grade của mình
        elif user.profile.role == 'student':
            return queryset.filter(student=user)
        
        return queryset.none()


class GradeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa grade
    """
    queryset = Grade.objects.select_related(
        'student', 'course', 'assignment', 'created_by'
    ).all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated, CanGradeAssignment]


# =============================================================================
# TAG & NOTE VIEWS
# =============================================================================

class TagListCreateView(generics.ListCreateAPIView):
    """
    List tags hoặc tạo tag mới
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa tag
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


class NoteListCreateView(generics.ListCreateAPIView):
    """
    List notes hoặc tạo note mới
    """
    queryset = Note.objects.prefetch_related('tags').select_related('user', 'course', 'assignment').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['priority', 'is_important', 'is_pinned', 'is_public', 'course']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-is_pinned', '-is_important', '-updated_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NoteCreateSerializer
        return NoteSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Chỉ xem note của mình và note public
        return queryset.filter(
            Q(user=user) | Q(is_public=True)
        )


class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Chi tiết, cập nhật, xóa note
    """
    queryset = Note.objects.prefetch_related('tags').select_related('user', 'course', 'assignment').all()
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


# =============================================================================
# ANALYTICS VIEWS
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def course_analytics(request, pk):
    """
    Analytics của một course
    """
    try:
        course = Course.objects.get(pk=pk)
        
        # Kiểm tra quyền
        user = request.user
        if (user.profile.role == 'teacher' and course.teacher != user) or \
           (user.profile.role == 'student' and not course.students.filter(id=user.id).exists()):
            if user.profile.role != 'admin':
                return Response({
                    'error': 'Không có quyền truy cập.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        enrollments = course.enrollments.all()
        grades = course.grades.all()
        
        analytics_data = {
            'total_students': enrollments.count(),
            'active_students': enrollments.filter(status='enrolled').count(),
            'completed_students': enrollments.filter(status='completed').count(),
            'dropped_students': enrollments.filter(status='dropped').count(),
            'average_grade': grades.aggregate(avg=Avg('score'))['avg'] or 0,
            'assignment_count': course.assignments.count(),
            'completion_rate': 0
        }
        
        if analytics_data['total_students'] > 0:
            analytics_data['completion_rate'] = (
                analytics_data['completed_students'] / analytics_data['total_students'] * 100
            )
        
        serializer = CourseAnalyticsSerializer(analytics_data)
        return Response(serializer.data)
        
    except Course.DoesNotExist:
        return Response({
            'error': 'Không tìm thấy course.'
        }, status=status.HTTP_404_NOT_FOUND) 