"""
Study Management API Serializers
"""
from rest_framework import serializers
from core.models import Course, CourseEnrollment, Assignment, AssignmentSubmission, Grade, Tag, Note
from .user_serializers import UserSerializer
from django.contrib.auth.models import User


class TagSerializer(serializers.ModelSerializer):
    """Serializer cho Tag"""
    note_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'description', 'note_count', 'created_at']
        read_only_fields = ['created_at']
    
    def get_note_count(self, obj):
        return obj.notes.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CourseSerializer(serializers.ModelSerializer):
    """Serializer cho Course"""
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    assistant_teacher_ids = serializers.PrimaryKeyRelatedField(
        source='assistant_teachers', many=True, read_only=True
    )
    academic_year_name = serializers.CharField(source='academic_year.name', read_only=True)
    student_count = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    semester_display = serializers.CharField(source='get_semester_display', read_only=True)
    assignment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'code', 'description', 'credits', 'semester', 'semester_display',
            'academic_year', 'academic_year_name', 'start_date', 'end_date', 'teacher', 'teacher_name',
            'status', 'status_display', 'max_students', 'syllabus', 'student_count',
            'is_active', 'is_full', 'assignment_count', 'assistant_teacher_ids', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_student_count(self, obj):
        """Số lượng sinh viên đã đăng ký (chỉ status enrolled)"""
        return obj.enrolled_student_count

    def validate(self, attrs):
        teacher = attrs.get('teacher') or getattr(self.instance, 'teacher', None)
        if teacher and (not hasattr(teacher, 'profile') or teacher.profile.role != 'teacher'):
            raise serializers.ValidationError({'teacher': 'Người được chọn không có vai trò giảng viên.'})
        return super().validate(attrs)

    def get_assignment_count(self, obj):
        return obj.assignments.count()


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer cho CourseEnrollment"""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name', 'course_code',
            'status', 'status_display', 'enrolled_at', 'dropped_at', 
            'final_grade', 'notes'
        ]
        read_only_fields = ['enrolled_at', 'dropped_at']


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer cho Assignment"""
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_assignment_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    is_overdue = serializers.ReadOnlyField()
    is_submission_open = serializers.ReadOnlyField()
    submission_count = serializers.ReadOnlyField()
    graded_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'course', 'course_name', 'course_code',
            'assignment_type', 'type_display', 'priority', 'priority_display',
            'status', 'status_display', 'created_at', 'published_at', 'due_date',
            'submission_deadline', 'max_score', 'weight', 'attachment',
            'allow_late_submission', 'max_submissions', 'is_anonymous',
            'created_by', 'created_by_name', 'updated_at', 'is_overdue',
            'is_submission_open', 'submission_count', 'graded_count'
        ]
        read_only_fields = ['created_at', 'published_at', 'updated_at', 'created_by']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    """Serializer cho AssignmentSubmission"""
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'id', 'assignment', 'assignment_title', 'student', 'student_name',
            'status', 'status_display', 'content', 'attachment', 'submitted_at',
            'graded_at', 'score', 'feedback', 'submission_number', 'is_late'
        ]
        read_only_fields = ['submitted_at', 'graded_at', 'is_late', 'student']
    
    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class GradeSerializer(serializers.ModelSerializer):
    """Serializer cho Grade"""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    grade_type_display = serializers.CharField(source='get_grade_type_display', read_only=True)
    
    percentage = serializers.ReadOnlyField()
    letter_grade = serializers.ReadOnlyField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name', 'course_code',
            'assignment', 'assignment_title', 'submission', 'grade_type', 
            'grade_type_display', 'score', 'max_score', 'weight', 'date',
            'comment', 'is_final', 'created_by', 'created_by_name',
            'percentage', 'letter_grade', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class NoteSerializer(serializers.ModelSerializer):
    """Serializer cho Note"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    preview = serializers.ReadOnlyField()
    tag_names = serializers.ReadOnlyField()
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    
    class Meta:
        model = Note
        fields = [
            'id', 'user', 'user_name', 'title', 'content', 'preview',
            'tags', 'tag_names', 'tags_detail', 'priority', 'priority_display',
            'is_important', 'is_pinned', 'is_public', 'course', 'course_name',
            'assignment', 'assignment_title', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NoteCreateSerializer(serializers.ModelSerializer):
    """Serializer để tạo Note với tags"""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Note
        fields = [
            'title', 'content', 'priority', 'is_important', 
            'is_pinned', 'is_public', 'course', 'assignment', 'tag_ids'
        ]
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['user'] = self.context['request'].user
        
        note = super().create(validated_data)
        
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            note.tags.set(tags)
        
        return note


# Serializers cho bulk operations và analytics
class BulkEnrollmentSerializer(serializers.Serializer):
    """Serializer cho đăng ký hàng loạt"""
    course_id = serializers.IntegerField()
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )


class CourseAnalyticsSerializer(serializers.Serializer):
    """Serializer cho analytics môn học"""
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    completed_students = serializers.IntegerField()
    dropped_students = serializers.IntegerField()
    average_grade = serializers.DecimalField(max_digits=5, decimal_places=2)
    assignment_count = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class StudentPerformanceSerializer(serializers.Serializer):
    """Serializer cho hiệu suất sinh viên"""
    student = UserSerializer()
    total_courses = serializers.IntegerField()
    completed_courses = serializers.IntegerField()
    average_grade = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_assignments = serializers.IntegerField()
    submitted_assignments = serializers.IntegerField()
    graded_assignments = serializers.IntegerField()
    submission_rate = serializers.DecimalField(max_digits=5, decimal_places=2) 