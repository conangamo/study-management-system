"""
Forms for Assignment system
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import os
from django.db.models import Q

from ..models.assignment import Assignment, AssignmentFile, AssignmentSubmission, AssignmentGrade
from ..models.study import Course


class AssignmentForm(forms.ModelForm):
    """Form tạo/chỉnh sửa bài tập"""
    
    # File upload fields
    assignment_files = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif'
        }),
        help_text='Chọn file đính kèm bài tập (PDF, DOC, DOCX, TXT, JPG, PNG, GIF)'
    )
    
    # Custom fields for better UX
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'min': timezone.now().strftime('%Y-%m-%dT%H:%M')
            }
        ),
        help_text='Chọn ngày và giờ hạn nộp'
    )
    
    allowed_file_types = forms.MultipleChoiceField(
        choices=[
            ('.pdf', 'PDF'),
            ('.doc', 'DOC'),
            ('.docx', 'DOCX'),
            ('.txt', 'TXT'),
            ('.jpg', 'JPG'),
            ('.jpeg', 'JPEG'),
            ('.png', 'PNG'),
            ('.gif', 'GIF'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text='Chọn loại file được phép nộp'
    )
    
    class Meta:
        model = Assignment
        fields = [
            'course', 'title', 'description', 'instructions',
            'due_date', 'max_score', 'status', 'allow_late_submission',
            'max_file_size', 'is_visible_to_students'
        ]
        widgets = {
            'course': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Chọn môn học'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề bài tập'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mô tả chi tiết bài tập'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Hướng dẫn làm bài (tùy chọn)'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.1
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'allow_late_submission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_file_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'is_visible_to_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses based on user role
        if user:
            if user.is_superuser:
                # Admin can see all courses
                self.fields['course'].queryset = Course.objects.filter(status='active')
            elif hasattr(user, 'profile') and user.profile.role == 'teacher':
                # Teacher can only see their courses
                self.fields['course'].queryset = Course.objects.filter(
                    Q(teacher=user) | Q(assistant_teachers=user),
                    status='active'
                )
            else:
                # Other users cannot create assignments
                self.fields['course'].queryset = Course.objects.none()
        
        # Set initial values
        if not self.instance.pk:  # New assignment
            self.fields['allowed_file_types'].initial = ['.pdf', '.doc', '.docx']
            self.fields['status'].initial = 'draft'
            self.fields['max_score'].initial = 10.0
            self.fields['max_file_size'].initial = 10
        
        # Add help text
        self.fields['course'].help_text = 'Chọn môn học bạn phụ trách'
        self.fields['title'].help_text = 'Tiêu đề ngắn gọn, rõ ràng'
        self.fields['description'].help_text = 'Mô tả chi tiết yêu cầu bài tập'
        self.fields['max_score'].help_text = 'Điểm tối đa cho bài tập này'
        self.fields['max_file_size'].help_text = 'Kích thước file tối đa (MB)'
    
    def clean_due_date(self):
        """Validate due date"""
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date <= timezone.now():
            raise ValidationError('Hạn nộp phải trong tương lai.')
        return due_date
    
    def clean_max_score(self):
        """Validate max score"""
        max_score = self.cleaned_data.get('max_score')
        if max_score and max_score <= 0:
            raise ValidationError('Điểm tối đa phải lớn hơn 0.')
        return max_score
    
    def clean_max_file_size(self):
        """Validate max file size"""
        max_file_size = self.cleaned_data.get('max_file_size')
        if max_file_size and max_file_size <= 0:
            raise ValidationError('Kích thước file tối đa phải lớn hơn 0.')
        return max_file_size
    
    def clean(self):
        """Clean form data"""
        cleaned_data = super().clean()
        
        # Convert allowed_file_types to JSON
        allowed_types = cleaned_data.get('allowed_file_types')
        if allowed_types:
            cleaned_data['allowed_file_types'] = list(allowed_types)
        
        return cleaned_data


class AssignmentFileUploadForm(forms.ModelForm):
    """Form upload file cho bài tập"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif'
        }),
        help_text='Chọn file để upload'
    )
    
    class Meta:
        model = AssignmentFile
        fields = ['file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mô tả file (tùy chọn)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.assignment = kwargs.pop('assignment', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError('Vui lòng chọn file.')
        
        # Check file size
        if self.assignment and self.assignment.max_file_size:
            max_size = self.assignment.max_file_size * 1024 * 1024  # Convert to bytes
            if file.size > max_size:
                raise ValidationError(
                    f'File quá lớn. Kích thước tối đa: {self.assignment.max_file_size} MB'
                )
        
        # Check file type
        if self.assignment and self.assignment.allowed_file_types:
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in self.assignment.allowed_file_types:
                raise ValidationError(
                    f'Loại file không được phép. Các loại file được phép: {", ".join(self.assignment.allowed_file_types)}'
                )
        
        return file
    
    def save(self, commit=True):
        """Override save to set assignment and user"""
        instance = super().save(commit=False)
        if self.assignment:
            instance.assignment = self.assignment
        if self.user:
            instance.uploaded_by = self.user
        if commit:
            instance.save()
        return instance


class AssignmentSubmissionForm(forms.ModelForm):
    """Form nộp bài tập"""
    
    submission_files = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar'
        }),
        help_text='Chọn file bài làm (PDF, DOC, DOCX, TXT, JPG, PNG, GIF, ZIP, RAR)'
    )
    
    class Meta:
        model = AssignmentSubmission
        fields = ['comments']
        widgets = {
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú về bài làm (tùy chọn)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.assignment = kwargs.pop('assignment', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
    
    def clean_submission_files(self):
        """Validate submission files"""
        files = self.files.getlist('submission_files')
        
        if not files:
            raise ValidationError('Vui lòng chọn ít nhất một file để nộp.')
        
        # Check each file
        for file in files:
            # Check file size
            if self.assignment and self.assignment.max_file_size:
                max_size = self.assignment.max_file_size * 1024 * 1024
                if file.size > max_size:
                    raise ValidationError(
                        f'File {file.name} quá lớn. Kích thước tối đa: {self.assignment.max_file_size} MB'
                    )
            
            # Check file type
            if self.assignment and self.assignment.allowed_file_types:
                file_ext = os.path.splitext(file.name)[1].lower()
                if file_ext not in self.assignment.allowed_file_types:
                    raise ValidationError(
                        f'File {file.name} có loại không được phép. Các loại file được phép: {", ".join(self.assignment.allowed_file_types)}'
                    )
        
        return files
    
    def save(self, commit=True):
        """Override save to set assignment and student"""
        instance = super().save(commit=False)
        if self.assignment:
            instance.assignment = self.assignment
        if self.student:
            instance.student = self.student
        if commit:
            instance.save()
        return instance


class AssignmentGradeForm(forms.ModelForm):
    """Form chấm điểm bài tập"""
    
    class Meta:
        model = AssignmentGrade
        fields = ['score', 'feedback', 'is_final', 'criteria_scores', 'rubric_used']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nhận xét chi tiết về bài làm'
            }),
            'is_final': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'criteria_scores': forms.HiddenInput(),
            'rubric_used': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.submission = kwargs.pop('submission', None)
        self.grader = kwargs.pop('grader', None)
        super().__init__(*args, **kwargs)
        
        # Set max score based on assignment
        if self.submission and self.submission.assignment:
            max_score = self.submission.assignment.max_score
            self.fields['score'].widget.attrs['max'] = max_score
            self.fields['score'].help_text = f'Điểm tối đa: {max_score}'
    
    def clean_score(self):
        """Validate score"""
        score = self.cleaned_data.get('score')
        
        if score is not None:
            if score < 0:
                raise ValidationError('Điểm số không được âm.')
            
            if self.submission and self.submission.assignment:
                max_score = self.submission.assignment.max_score
                if score > max_score:
                    raise ValidationError(f'Điểm số không được vượt quá {max_score}.')
        
        return score
    
    def save(self, commit=True):
        """Override save to set submission and grader"""
        instance = super().save(commit=False)
        if self.submission:
            instance.submission = self.submission
        if self.grader:
            instance.graded_by = self.grader
        if commit:
            instance.save()
        return instance


class AssignmentSearchForm(forms.Form):
    """Form tìm kiếm bài tập"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm bài tập...'
        })
    )
    
    course_filter = forms.ModelChoiceField(
        queryset=Course.objects.filter(status='active'),
        required=False,
        empty_label="Tất cả môn học",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status_filter = forms.ChoiceField(
        choices=[
            ('', 'Tất cả trạng thái'),
            ('draft', 'Bản nháp'),
            ('active', 'Hoạt động'),
            ('inactive', 'Không hoạt động'),
            ('closed', 'Đã đóng'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_filter = forms.ChoiceField(
        choices=[
            ('', 'Tất cả thời gian'),
            ('today', 'Hôm nay'),
            ('week', 'Tuần này'),
            ('month', 'Tháng này'),
            ('overdue', 'Quá hạn'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AssignmentSubmissionSearchForm(forms.Form):
    """Form tìm kiếm bài nộp"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm bài nộp...'
        })
    )
    
    status_filter = forms.ChoiceField(
        choices=[
            ('', 'Tất cả trạng thái'),
            ('submitted', 'Đã nộp'),
            ('late', 'Nộp muộn'),
            ('graded', 'Đã chấm điểm'),
            ('returned', 'Đã trả bài'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    grade_filter = forms.ChoiceField(
        choices=[
            ('', 'Tất cả điểm'),
            ('graded', 'Đã chấm điểm'),
            ('not_graded', 'Chưa chấm điểm'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    ) 