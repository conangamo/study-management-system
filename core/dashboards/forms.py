"""
Forms for Dashboard Views
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime

from core.models import Course, Assignment, Grade, Note, Tag, UserProfile, UserRole


class DashboardCourseForm(forms.ModelForm):
    """Form tạo/sửa môn học trong dashboard"""
    
    class Meta:
        model = Course
        fields = [
            'name', 'code', 'description', 'credits', 'semester', 
            'academic_year', 'start_date', 'end_date', 'max_students', 
            'syllabus', 'requirements'
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
            'semester': forms.Select(attrs={
                'class': 'form-select'
            }),
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
            'max_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 200
            }),
            'syllabus': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Giáo trình môn học'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Yêu cầu tiên quyết'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu')
        
        return cleaned_data


class DashboardAssignmentForm(forms.ModelForm):
    """Form tạo/sửa bài tập trong dashboard"""
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'course', 'assignment_type', 
            'priority', 'due_date', 'submission_deadline', 
            'max_score', 'weight', 'instructions', 'max_submissions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiêu đề bài tập'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mô tả chi tiết bài tập'
            }),
            'course': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assignment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'submission_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1,
                'step': 0.01
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Hướng dẫn làm bài'
            }),
            'max_submissions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Chỉ hiển thị courses của teacher hiện tại
        if user and hasattr(user, 'teaching_courses'):
            self.fields['course'].queryset = user.teaching_courses.all()
    
    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        submission_deadline = cleaned_data.get('submission_deadline')
        
        if due_date and submission_deadline:
            if due_date > submission_deadline:
                raise ValidationError('Hạn cuối nộp bài phải sau hạn nộp thường')
        
        return cleaned_data


class DashboardGradeForm(forms.ModelForm):
    """Form nhập điểm trong dashboard"""
    
    class Meta:
        model = Grade
        fields = [
            'student', 'course', 'assignment', 'grade_type', 
            'score', 'max_score', 'weight', 'comment', 'date'
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'course': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assignment': forms.Select(attrs={
                'class': 'form-select'
            }),
            'grade_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 1,
                'step': 0.01
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhận xét (tùy chọn)'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Chỉ hiển thị courses của teacher hiện tại
        if user and hasattr(user, 'teaching_courses'):
            courses = user.teaching_courses.all()
            self.fields['course'].queryset = courses
            
            # Chỉ hiển thị students trong courses của teacher
            from core.models import CourseEnrollment
            enrolled_students = User.objects.filter(
                enrollments__course__in=courses,
                enrollments__status='enrolled'
            ).distinct()
            self.fields['student'].queryset = enrolled_students
            
            # Chỉ hiển thị assignments của teacher
            self.fields['assignment'].queryset = Assignment.objects.filter(
                course__in=courses
            )
    
    def clean(self):
        cleaned_data = super().clean()
        score = cleaned_data.get('score')
        max_score = cleaned_data.get('max_score')
        
        if score and max_score:
            if score > max_score:
                raise ValidationError('Điểm không được vượt quá điểm tối đa')
        
        return cleaned_data


class DashboardNoteForm(forms.ModelForm):
    """Form tạo/sửa ghi chú trong dashboard"""
    
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tags cách nhau bằng dấu phẩy'
        }),
        help_text='Các tags cách nhau bằng dấu phẩy (VD: quan-trong, deadline, ghi-nho)'
    )
    
    class Meta:
        model = Note
        fields = ['title', 'content', 'is_pinned', 'course']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiêu đề ghi chú'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Nội dung ghi chú'
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'course': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Chỉ hiển thị courses mà user có liên quan
        if user:
            if hasattr(user, 'teaching_courses'):
                # Teacher - hiển thị courses đang dạy
                self.fields['course'].queryset = user.teaching_courses.all()
            elif hasattr(user, 'enrolled_courses'):
                # Student - hiển thị courses đã đăng ký
                from core.models import CourseEnrollment
                enrolled_courses = Course.objects.filter(
                    enrollments__student=user,
                    enrollments__status='enrolled'
                )
                self.fields['course'].queryset = enrolled_courses
        
        # Nếu đang edit, load tags hiện tại
        if self.instance.pk:
            current_tags = self.instance.tags.all().values_list('name', flat=True)
            self.fields['tags_input'].initial = ', '.join(current_tags)
    
    def save(self, commit=True):
        note = super().save(commit=commit)
        
        if commit:
            # Xử lý tags
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                
                # Xóa tags cũ
                note.tags.clear()
                
                # Thêm tags mới
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    note.tags.add(tag)
        
        return note


class DashboardUserForm(forms.ModelForm):
    """Form tạo/sửa user trong admin dashboard"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu'
        }),
        required=False,
        help_text='Để trống nếu không muốn thay đổi mật khẩu'
    )
    
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=False
    )
    
    student_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mã sinh viên (chỉ dành cho sinh viên)'
        })
    )
    
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số điện thoại'
        })
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên đăng nhập'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Nếu đang edit user, load thông tin profile
        if self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['role'].initial = profile.role
                self.fields['student_id'].initial = profile.student_id
                self.fields['phone_number'].initial = profile.phone_number
                self.fields['date_of_birth'].initial = profile.date_of_birth
            except UserProfile.DoesNotExist:
                pass
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        
        if commit:
            # Đổi mật khẩu nếu có
            password = self.cleaned_data.get('password')
            if password:
                user.set_password(password)
                user.save()
            
            # Tạo hoặc cập nhật profile
            role = self.cleaned_data.get('role')
            if role:
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': role}
                )
                
                if not created:
                    profile.role = role
                
                # Cập nhật thông tin profile
                profile.student_id = self.cleaned_data.get('student_id', '')
                profile.phone_number = self.cleaned_data.get('phone_number', '')
                profile.date_of_birth = self.cleaned_data.get('date_of_birth')
                profile.save()
        
        return user


class BulkGradeForm(forms.Form):
    """Form chấm điểm hàng loạt"""
    
    assignment = forms.ModelChoiceField(
        queryset=Assignment.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_assignment_select'
        }),
        label='Chọn bài tập'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'teaching_courses'):
            # Chỉ hiển thị assignments của teacher
            self.fields['assignment'].queryset = Assignment.objects.filter(
                course__teacher=user,
                status__in=['submission_closed', 'graded']
            ).select_related('course')


class CourseEnrollmentForm(forms.Form):
    """Form đăng ký môn học hàng loạt"""
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(status='active'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Chọn môn học'
    )
    
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            profile__role__name='student'
        ),
        widget=forms.CheckboxSelectMultiple(),
        label='Chọn sinh viên'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Chỉ hiển thị students chưa đăng ký môn học nào
        self.fields['students'].queryset = User.objects.filter(
            profile__role__name='student',
            is_active=True
        ).order_by('last_name', 'first_name') 