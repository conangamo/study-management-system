"""
Teacher Dashboard Forms
- Course management forms
- Assignment management forms  
- Grade management forms
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from core.models.study import Course, Grade
from core.models.assignment import Assignment, AssignmentSubmission
from core.models.user import UserProfile


class TeacherCourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    
    class Meta:
        model = Course
        fields = [
            'name', 'code', 'description', 'credits', 'semester', 
            'academic_year', 'start_date', 'end_date', 'status',
            'max_students', 'syllabus'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên môn học'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mã môn học (VD: CS101)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả môn học'
            }),
            'credits': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2023-2024'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'max_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'syllabus': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Nội dung giảng dạy chi tiết'
            }),
        }
    
    def clean_academic_year(self):
        """Validate academic year format"""
        academic_year = self.cleaned_data.get('academic_year')
        if academic_year:
            import re
            if not re.match(r'^\d{4}-\d{4}$', academic_year):
                raise ValidationError('Năm học phải có định dạng YYYY-YYYY (VD: 2023-2024)')
        return academic_year
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu.')
        
        return cleaned_data


class TeacherAssignmentForm(forms.ModelForm):
    """Form for creating/editing assignments"""
    
    class Meta:
        model = Assignment
        fields = [
            'course', 'title', 'description', 'due_date', 
            'max_score', 'attachment', 'instructions',
            'allow_late_submission', 'max_file_size', 'allowed_file_types',
            'is_visible_to_students', 'status'
        ]
        widgets = {
            'course': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiêu đề bài tập',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mô tả chi tiết bài tập',
                'required': True
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1,
                'value': 10.0
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.png,.jpg,.jpeg'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Hướng dẫn làm bài (tùy chọn)'
            }),
            'allow_late_submission': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'max_file_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 10,
                'help_text': 'Kích thước file tối đa (MB)'
            }),
            'is_visible_to_students': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
         
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Show courses where user is either main teacher or assistant teacher
            self.fields['course'].queryset = Course.objects.filter(
                Q(teacher=teacher) | Q(assistant_teachers=teacher)
            ).distinct()
            
        # Set default allowed file types
        if not self.instance.pk:
            self.fields['allowed_file_types'].initial = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg']
    
    def clean_attachment(self):
        """Validate uploaded file"""
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Check file size (convert MB to bytes)
            max_size = self.cleaned_data.get('max_file_size', 10) * 1024 * 1024
            if attachment.size > max_size:
                raise ValidationError(f'File quá lớn. Kích thước tối đa là {max_size/(1024*1024):.0f}MB.')
            
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg']
            file_extension = attachment.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise ValidationError(f'Loại file không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}')
        
        return attachment
    
    def clean_due_date(self):
        """Validate due date is in the future"""
        due_date = self.cleaned_data.get('due_date')
        
        if due_date and due_date <= timezone.now():
            raise ValidationError('Hạn nộp phải trong tương lai.')
        
        return due_date
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Set allowed file types if not set
        if not cleaned_data.get('allowed_file_types'):
            cleaned_data['allowed_file_types'] = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg']
        
        return cleaned_data


class TeacherGradeForm(forms.ModelForm):
    """Form for creating/editing grades"""
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        if teacher:
            # Only show students and courses related to this teacher
            self.fields['student'].queryset = User.objects.filter(
                Q(enrolled_courses__teacher=teacher) | Q(enrolled_courses__assistant_teachers=teacher),
                profile__role='student'
            ).distinct()
            
            self.fields['course'].queryset = Course.objects.filter(
                Q(teacher=teacher) | Q(assistant_teachers=teacher)
            ).distinct()
            
            self.fields['assignment'].queryset = Assignment.objects.filter(
                Q(course__teacher=teacher) | Q(course__assistant_teachers=teacher)
            ).distinct()
            
            # Make assignment optional initially
            self.fields['assignment'].required = False
    
    class Meta:
        model = Grade
        fields = [
            'student', 'course', 'assignment', 'grade_type',
            'score', 'max_score', 'weight', 'date', 'comment'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'assignment': forms.Select(attrs={'class': 'form-select'}),
            'grade_type': forms.Select(attrs={'class': 'form-select'}),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1,
                'value': 10.0
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1,
                'value': 1.0
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'value': timezone.now().date()
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhận xét (tùy chọn)'
            }),
        }
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')
        assignment = cleaned_data.get('assignment')
        score = cleaned_data.get('score')
        max_score = cleaned_data.get('max_score')
        
        # Check if student is enrolled in course
        if student and course:
            if not course.students.filter(id=student.id).exists():
                raise ValidationError('Sinh viên không đăng ký môn học này.')
        
        # Check if assignment belongs to course
        if assignment and course:
            if assignment.course != course:
                raise ValidationError('Bài tập không thuộc môn học đã chọn.')
        
        # Check score validity
        if score is not None and max_score is not None:
            if score > max_score:
                raise ValidationError('Điểm không được vượt quá điểm tối đa.')
        
        return cleaned_data


class TeacherBulkGradeForm(forms.Form):
    """Form for bulk grade entry"""
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Môn học'
    )
    
    assignment = forms.ModelChoiceField(
        queryset=Assignment.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Bài tập (tùy chọn)'
    )
    
    grade_type = forms.ChoiceField(
        choices=Grade.GRADE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Loại điểm'
    )
    
    max_score = forms.DecimalField(
        initial=10.0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.1
        }),
        label='Điểm tối đa'
    )
    
    weight = forms.DecimalField(
        initial=1.0,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.1
        }),
        label='Trọng số'
    )
    
    date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Ngày chấm điểm'
    )
    
    grades_json = forms.CharField(
        widget=forms.HiddenInput(),
        label='Dữ liệu điểm (JSON)'
    )
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(
                Q(teacher=teacher) | Q(assistant_teachers=teacher)
            ).distinct()
            self.fields['assignment'].queryset = Assignment.objects.filter(
                Q(course__teacher=teacher) | Q(course__assistant_teachers=teacher)
            ).distinct()


class TeacherAssignmentGradingForm(forms.Form):
    """Form for grading individual assignment submissions"""
    
    submission_id = forms.IntegerField(widget=forms.HiddenInput())
    
    score = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.1,
            'placeholder': 'Điểm'
        }),
        label='Điểm số'
    )
    
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Nhận xét cho sinh viên'
        }),
        label='Nhận xét'
    )
    
    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        
        if assignment:
            self.fields['score'].widget.attrs['max'] = str(assignment.max_score)
            self.fields['score'].help_text = f'Điểm tối đa: {assignment.max_score}'


class CourseStudentEnrollmentForm(forms.Form):
    """Form for enrolling students in course"""
    
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Chọn sinh viên'
    )
    
    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        if course:
            # Show students not yet enrolled in this course
            enrolled_students = course.students.all()
            self.fields['students'].queryset = User.objects.filter(
                profile__role='student'
            ).exclude(
                id__in=enrolled_students.values_list('id', flat=True)
            )


class AssignmentStatusForm(forms.Form):
    """Form for changing assignment status"""
    
    status = forms.ChoiceField(
        choices=Assignment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Trạng thái'
    )
    
    def __init__(self, *args, **kwargs):
        assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        
        if assignment:
            self.fields['status'].initial = assignment.status 