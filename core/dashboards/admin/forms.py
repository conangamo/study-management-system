"""
Admin Dashboard Forms
- User management forms
- Import/Export forms
- System management forms
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from core.models.user import UserProfile
from core.models.study import Course, Class
from core.models.academic import AcademicYear


class AdminUserCreateForm(UserCreationForm):
    """Form for creating new users by admin"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Họ'
        })
    )
    
    # Profile fields
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.ChoiceField(
        choices=[('', '--- Chọn khoa ---')] + UserProfile.DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    student_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mã sinh viên (chỉ dành cho sinh viên)'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số điện thoại'
        })
    )
    
    year_of_study = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Năm học (2023)'
        })
    )
    
    class_enrolled = forms.ModelChoiceField(
        queryset=Class.objects.filter(status='active').order_by('-academic_year', 'department', 'class_number'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn lớp học...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1',
            'data-ajax--url': '/custom-admin/classes/search/',
            'data-ajax--data-type': 'json',
            'data-ajax--delay': '250'
        }),
        label='Lớp học',
        help_text='Chọn lớp học cho sinh viên. Gõ để tìm kiếm theo tên lớp hoặc khoa.',
        empty_label='-- Chọn lớp học --'
    )
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Giới thiệu'
        })
    )
    
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên đăng nhập'
            }),
        }
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Email này đã được sử dụng.')
        return email
    
    def clean_student_id(self):
        """Validate student ID"""
        student_id = self.cleaned_data.get('student_id')
        role = self.cleaned_data.get('role')
        
        if role == 'student' and not student_id:
            raise ValidationError('Sinh viên phải có mã sinh viên.')
        
        if student_id and UserProfile.objects.filter(student_id=student_id).exists():
            raise ValidationError('Mã sinh viên này đã được sử dụng.')
        
        return student_id
    
    def save(self, commit=True):
        """Save user and create profile"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = self.cleaned_data['is_active']
        
        if commit:
            user.save()
            
            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                department=self.cleaned_data.get('department', ''),
                student_id=self.cleaned_data.get('student_id', ''),
                phone=self.cleaned_data.get('phone', ''),
                year_of_study=self.cleaned_data.get('year_of_study'),
                bio=self.cleaned_data.get('bio', ''),
            )
            
            # Assign to class if selected
            class_enrolled = self.cleaned_data.get('class_enrolled')
            if class_enrolled and self.cleaned_data['role'] == 'student':
                profile.class_enrolled = class_enrolled
                profile.save()
        
        return user


class AdminUserUpdateForm(forms.ModelForm):
    """Form for updating user information by admin"""
    
    # Profile fields
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.ChoiceField(
        choices=[('', '--- Chọn khoa ---')] + UserProfile.DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    student_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mã sinh viên'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số điện thoại'
        })
    )
    
    year_of_study = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Năm học'
        })
    )
    
    class_enrolled = forms.ModelChoiceField(
        queryset=Class.objects.filter(status='active').order_by('-academic_year', 'department', 'class_number'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn lớp học...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1',
            'data-ajax--url': '/custom-admin/classes/search/',
            'data-ajax--data-type': 'json',
            'data-ajax--delay': '250'
        }),
        label='Lớp học',
        help_text='Chọn lớp học cho sinh viên. Gõ để tìm kiếm theo tên lớp hoặc khoa.',
        empty_label='-- Chọn lớp học --'
    )
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Giới thiệu'
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
                'placeholder': 'Tên'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate profile fields if instance exists
        if self.instance and hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['role'].initial = profile.role
            self.fields['department'].initial = profile.department
            self.fields['student_id'].initial = profile.student_id
            self.fields['phone'].initial = profile.phone
            self.fields['year_of_study'].initial = profile.year_of_study
            self.fields['class_enrolled'].initial = profile.class_enrolled
            self.fields['bio'].initial = profile.bio
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Email này đã được sử dụng.')
        return email
    
    def clean_student_id(self):
        """Validate student ID"""
        student_id = self.cleaned_data.get('student_id')
        role = self.cleaned_data.get('role')
        
        if role == 'student' and not student_id:
            raise ValidationError('Sinh viên phải có mã sinh viên.')
        
        if student_id:
            existing = UserProfile.objects.filter(student_id=student_id)
            if self.instance and hasattr(self.instance, 'profile'):
                existing = existing.exclude(pk=self.instance.profile.pk)
            
            if existing.exists():
                raise ValidationError('Mã sinh viên này đã được sử dụng.')
        
        return student_id
    
    def save(self, commit=True):
        """Save user and update profile"""
        user = super().save(commit)
        
        if commit and hasattr(user, 'profile'):
            # Update profile
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.department = self.cleaned_data.get('department', '')
            profile.student_id = self.cleaned_data.get('student_id', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.year_of_study = self.cleaned_data.get('year_of_study')
            profile.class_enrolled = self.cleaned_data.get('class_enrolled')
            profile.bio = self.cleaned_data.get('bio', '')
            profile.save()
        
        return user


class AdminUserImportForm(forms.Form):
    """Form for importing users from CSV"""
    
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text='Tải lên file CSV với các cột: username, email, first_name, last_name, role, student_id, department, phone'
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Ghi đè thông tin người dùng đã tồn tại'
    )
    
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Gửi email chào mừng cho người dùng mới'
    )
    
    def clean_csv_file(self):
        """Validate CSV file"""
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file.name.endswith('.csv'):
            raise ValidationError('File phải có định dạng CSV.')
        
        if csv_file.size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError('File không được vượt quá 5MB.')
        
        return csv_file


class AdminBulkUserActionForm(forms.Form):
    """Form for bulk actions on users"""
    
    ACTION_CHOICES = [
        ('', '--- Chọn hành động ---'),
        ('activate', 'Kích hoạt'),
        ('deactivate', 'Vô hiệu hóa'),
        ('delete', 'Xóa'),
        ('reset_password', 'Đặt lại mật khẩu'),
        ('send_email', 'Gửi email'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    user_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    # Optional fields for specific actions
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu mới'
        }),
        help_text='Chỉ cần thiết khi đặt lại mật khẩu'
    )
    
    email_subject = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tiêu đề email'
        })
    )
    
    email_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Nội dung email'
        })
    )
    
    def clean_user_ids(self):
        """Validate and convert user IDs"""
        user_ids_str = self.cleaned_data.get('user_ids')
        
        if not user_ids_str:
            raise ValidationError('Vui lòng chọn ít nhất một người dùng.')
        
        try:
            user_ids = [int(id.strip()) for id in user_ids_str.split(',') if id.strip()]
            
            if not user_ids:
                raise ValidationError('Không có người dùng nào được chọn.')
            
            # Verify users exist
            existing_count = User.objects.filter(id__in=user_ids).count()
            if existing_count != len(user_ids):
                raise ValidationError('Một số người dùng không tồn tại.')
            
            return user_ids
            
        except ValueError:
            raise ValidationError('ID người dùng không hợp lệ.')
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        # Validate required fields for specific actions
        if action == 'reset_password' and not cleaned_data.get('new_password'):
            raise ValidationError('Vui lòng nhập mật khẩu mới.')
        
        if action == 'send_email':
            if not cleaned_data.get('email_subject'):
                raise ValidationError('Vui lòng nhập tiêu đề email.')
            if not cleaned_data.get('email_message'):
                raise ValidationError('Vui lòng nhập nội dung email.')
        
        return cleaned_data


class AdminResetPasswordForm(forms.Form):
    """Form for resetting user password by admin"""
    
    new_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu mới'
        })
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Xác nhận mật khẩu'
        })
    )
    
    send_notification = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Gửi thông báo đến email của người dùng'
    )
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('Mật khẩu xác nhận không khớp.')
        
        return cleaned_data


class AdminSystemSettingsForm(forms.Form):
    """Form for system settings"""
    
    site_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên website'
        })
    )
    
    site_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Mô tả website'
        })
    )
    
    allow_registration = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Cho phép người dùng tự đăng ký tài khoản'
    )
    
    require_email_verification = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Yêu cầu xác thực email khi đăng ký'
    )
    
    default_user_role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Vai trò mặc định cho người dùng mới'
    )
    
    max_file_upload_size = forms.IntegerField(
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'MB'
        }),
        help_text='Kích thước file tối đa có thể tải lên (MB)'
    )
    
    session_timeout = forms.IntegerField(
        min_value=30,
        max_value=1440,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phút'
        }),
        help_text='Thời gian hết hạn phiên đăng nhập (phút)'
    )
    
    maintenance_mode = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Kích hoạt chế độ bảo trì'
    )
    
    maintenance_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Thông báo bảo trì'
        })
    )


class AdminDatabaseBackupForm(forms.Form):
    """Form for database backup settings"""
    
    backup_type = forms.ChoiceField(
        choices=[
            ('full', 'Backup toàn bộ'),
            ('data_only', 'Chỉ dữ liệu'),
            ('schema_only', 'Chỉ cấu trúc'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    include_media = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Bao gồm các file media'
    )
    
    compress = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Nén file backup'
    )
    
    notification_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email nhận thông báo'
        }),
        help_text='Email để nhận thông báo khi backup hoàn tất'
    ) 


class TeacherChoiceField(forms.ModelMultipleChoiceField):
    """Custom field to display teacher names with emails"""
    
    def label_from_instance(self, obj):
        """Display teacher name with email"""
        email = getattr(obj, 'email', '')
        department = getattr(obj.profile, 'department', '') if hasattr(obj, 'profile') and obj.profile else ''
        
        if department:
            return f"{obj.get_full_name()} ({email}) - {department}"
        else:
            return f"{obj.get_full_name()} ({email})"


class AdminCourseForm(forms.ModelForm):
    """Form quản trị để tạo/chỉnh sửa môn học với các kiểm tra hợp lệ bổ sung"""

    teachers = TeacherChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2-multiple',
            'data-placeholder': 'Tìm và chọn giảng viên phụ trách...',
            'multiple': 'multiple',
            'id': 'teacher-select'
        }),
        label='Giảng viên phụ trách',
        help_text='Có thể chọn nhiều giảng viên phụ trách cho môn học này. Gõ để tìm kiếm theo tên hoặc email.',
        required=True
    )

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Môn tự chọn (không gắn năm học) —',
        label='Năm học'
    )

    class Meta:
        model = Course
        fields = [
            'name', 'code', 'description', 'credits', 'semester',
            'academic_year', 'start_date', 'end_date', 'status',
            'max_students', 'syllabus'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên môn học'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mã môn học (VD: CS101)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mô tả môn học'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'syllabus': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Nội dung giảng dạy chi tiết'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize the teachers queryset to include email in the display
        teachers_queryset = User.objects.filter(profile__role='teacher').select_related('profile')
        self.fields['teachers'].queryset = teachers_queryset
        
        # If editing existing course, set initial teachers
        if self.instance and self.instance.pk:
            # Get all teachers (main teacher + assistant teachers)
            all_teachers = []
            if self.instance.teacher:
                all_teachers.append(self.instance.teacher)
            all_teachers.extend(self.instance.assistant_teachers.all())
            self.fields['teachers'].initial = all_teachers

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            return name
        qs = Course.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Tên môn học đã tồn tại trong hệ thống.')
        return name

    def clean_teachers(self):
        teachers = self.cleaned_data.get('teachers')
        if not teachers:
            raise ValidationError('Phải chọn ít nhất một giảng viên phụ trách.')
        
        invalid = [u for u in teachers if not getattr(u, 'profile', None) or u.profile.role != 'teacher']
        if invalid:
            raise ValidationError('Tất cả người được chọn phải có vai trò giảng viên.')
        return teachers

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu.')
        return cleaned_data

    def save(self, commit=True):
        course = super().save(commit=False)
        
        if commit:
            # Get teachers from form data
            teachers = self.cleaned_data.get('teachers', [])
            
            if teachers:
                # Set the first teacher as main teacher (required field)
                course.teacher = teachers[0]
                course.save()
                
                # Add remaining teachers as assistant teachers
                remaining_teachers = list(teachers)[1:]
                if remaining_teachers:
                    course.assistant_teachers.set(remaining_teachers)
            else:
                # If no teachers selected, save without teacher (will be handled by validation)
                course.save()
        
        return course 


class AdminClassForm(forms.ModelForm):
    """Form cho admin tạo và chỉnh sửa lớp học"""
    
    # Custom fields for better UX
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ví dụ: 20IT1, 21KT2, Lớp A...'
        }),
        label='Tên lớp',
        help_text='Tên ngắn gọn của lớp. Để trống để tự động tạo theo format: năm học + khoa + số lớp.',
        required=False
    )
    
    display_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ví dụ: Lớp Công nghệ thông tin K20, Lớp Kế toán K21...'
        }),
        label='Tên hiển thị',
        help_text='Tên đầy đủ của lớp để hiển thị. Để trống để tự động tạo.',
        required=False
    )
    
    advisor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn cố vấn học tập...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1',
            'data-ajax--url': '/custom-admin/users/search/',
            'data-ajax--data-type': 'json',
            'data-ajax--delay': '250'
        }),
        label='Cố vấn học tập',
        required=False,
        help_text='Giảng viên cố vấn cho lớp học. Gõ để tìm kiếm theo tên hoặc email.',
        empty_label='-- Chọn cố vấn học tập --'
    )
    
    head_teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn giáo viên chủ nhiệm...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1',
            'data-ajax--url': '/custom-admin/users/search/',
            'data-ajax--data-type': 'json',
            'data-ajax--delay': '250'
        }),
        label='Giáo viên chủ nhiệm',
        required=False,
        help_text='Giáo viên chủ nhiệm của lớp. Gõ để tìm kiếm theo tên hoặc email.',
        empty_label='-- Chọn giáo viên chủ nhiệm --'
    )
    
    class Meta:
        model = Class
        fields = [
            'academic_year', 'department', 'class_number', 
            'advisor', 'head_teacher', 'max_students', 
            'status', 'description'
        ]
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Chọn năm học...'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select',
                'data-placeholder': 'Chọn khoa/ngành...'
            }),
            'class_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20',
                'placeholder': 'Nhập số lớp (1-20)'
            }),
            'max_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Nhập sĩ số tối đa'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Mô tả về lớp học (tùy chọn)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Optimize queryset for teachers with custom label
        teachers_queryset = User.objects.filter(
            profile__role='teacher'
        ).select_related('profile').order_by('first_name', 'last_name')
        
        # Custom label function to show name and email
        def teacher_label(user):
            full_name = user.get_full_name() or user.username
            email = user.email or 'Không có email'
            department = getattr(user.profile, 'department', '') if hasattr(user, 'profile') and user.profile else ''
            
            if department:
                return f"{full_name} ({email}) - {department}"
            else:
                return f"{full_name} ({email})"
        
        # Apply custom labels
        self.fields['advisor'].queryset = teachers_queryset
        self.fields['advisor'].label_from_instance = teacher_label
        
        self.fields['head_teacher'].queryset = teachers_queryset
        self.fields['head_teacher'].label_from_instance = teacher_label
        
        # Set initial values for display
        if self.instance and self.instance.pk:
            self.fields['advisor'].initial = self.instance.advisor
            self.fields['head_teacher'].initial = self.instance.head_teacher
    
    def clean(self):
        """Custom validation"""
        cleaned_data = super().clean()
        
        # Kiểm tra tên lớp không trùng lặp
        name = cleaned_data.get('name')
        if name:
            existing_class = Class.objects.filter(name=name)
            if self.instance and self.instance.pk:
                existing_class = existing_class.exclude(pk=self.instance.pk)
            
            if existing_class.exists():
                raise ValidationError({
                    'name': f'Tên lớp "{name}" đã tồn tại!'
                })
        
        academic_year = cleaned_data.get('academic_year')
        department = cleaned_data.get('department')
        class_number = cleaned_data.get('class_number')
        
        # Check if class already exists (theo academic_year, department, class_number)
        if academic_year and department and class_number:
            existing_class = Class.objects.filter(
                academic_year=academic_year,
                department=department,
                class_number=class_number
            )
            
            if self.instance and self.instance.pk:
                existing_class = existing_class.exclude(pk=self.instance.pk)
            
            if existing_class.exists():
                raise ValidationError(
                    f'Lớp với năm học {academic_year}, khoa {department}, số lớp {class_number} đã tồn tại!'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the class with proper handling"""
        class_obj = super().save(commit=False)
        
        if commit:
            class_obj.save()
            
            # Update many-to-many relationships
            self.save_m2m()
        
        return class_obj


class ClassSearchForm(forms.Form):
    """Form tìm kiếm và lọc lớp học"""
    
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm theo tên lớp, khoa...'
        }),
        label='Tìm kiếm'
    )
    
    academic_year_filter = forms.ChoiceField(
        choices=[('', 'Tất cả năm học')] + Class.YEAR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Năm học'
    )
    
    department_filter = forms.ChoiceField(
        choices=[('', 'Tất cả khoa')] + Class.DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Khoa/Ngành'
    )
    
    status_filter = forms.ChoiceField(
        choices=[('', 'Tất cả trạng thái')] + Class.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Trạng thái'
    )
    
    advisor_filter = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn cố vấn học tập...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1'
        }),
        label='Cố vấn học tập',
        empty_label='Tất cả cố vấn'
    )
    
    head_teacher_filter = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn giáo viên chủ nhiệm...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1'
        }),
        label='Giáo viên chủ nhiệm',
        empty_label='Tất cả GV chủ nhiệm'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Optimize teacher queryset with custom labels
        teachers_queryset = User.objects.filter(
            profile__role='teacher'
        ).select_related('profile').order_by('first_name', 'last_name')
        
        # Custom label function to show name and email
        def teacher_label(user):
            full_name = user.get_full_name() or user.username
            email = user.email or 'Không có email'
            department = getattr(user.profile, 'department', '') if hasattr(user, 'profile') and user.profile else ''
            
            if department:
                return f"{full_name} ({email}) - {department}"
            else:
                return f"{full_name} ({email})"
        
        # Apply custom labels
        self.fields['advisor_filter'].queryset = teachers_queryset
        self.fields['advisor_filter'].label_from_instance = teacher_label
        
        self.fields['head_teacher_filter'].queryset = teachers_queryset
        self.fields['head_teacher_filter'].label_from_instance = teacher_label


class BulkClassCreationForm(forms.Form):
    """Form tạo hàng loạt lớp học"""
    
    academic_year = forms.ChoiceField(
        choices=Class.YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Năm học',
        help_text='Năm sinh viên nhập học'
    )
    
    department = forms.ChoiceField(
        choices=Class.DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Khoa/Ngành'
    )
    
    start_class_number = forms.IntegerField(
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số lớp bắt đầu'
        }),
        label='Số lớp bắt đầu',
        help_text='Số thứ tự lớp đầu tiên (1-20)'
    )
    
    end_class_number = forms.IntegerField(
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số lớp kết thúc'
        }),
        label='Số lớp kết thúc',
        help_text='Số thứ tự lớp cuối cùng (1-20)'
    )
    
    max_students_per_class = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sĩ số tối đa mỗi lớp'
        }),
        label='Sĩ số tối đa mỗi lớp'
    )
    
    advisor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn cố vấn học tập...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1'
        }),
        label='Cố vấn học tập (chung)',
        help_text='Cố vấn học tập cho tất cả lớp (tùy chọn)',
        empty_label='-- Chọn cố vấn học tập --'
    )
    
    head_teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='teacher'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select select2-search',
            'data-placeholder': 'Tìm và chọn giáo viên chủ nhiệm...',
            'data-allow-clear': 'true',
            'data-minimum-input-length': '1'
        }),
        label='Giáo viên chủ nhiệm (chung)',
        help_text='Giáo viên chủ nhiệm cho tất cả lớp (tùy chọn)',
        empty_label='-- Chọn giáo viên chủ nhiệm --'
    )
    
    description_template = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Mô tả mẫu cho các lớp (có thể dùng {class_number} để thay thế)'
        }),
        label='Mô tả mẫu',
        help_text='Mô tả chung cho các lớp. Dùng {class_number} để thay thế số lớp.'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Optimize teacher queryset with custom labels
        teachers_queryset = User.objects.filter(
            profile__role='teacher'
        ).select_related('profile').order_by('first_name', 'last_name')
        
        # Custom label function to show name and email
        def teacher_label(user):
            full_name = user.get_full_name() or user.username
            email = user.email or 'Không có email'
            department = getattr(user.profile, 'department', '') if hasattr(user, 'profile') and user.profile else ''
            
            if department:
                return f"{full_name} ({email}) - {department}"
            else:
                return f"{full_name} ({email})"
        
        # Apply custom labels
        self.fields['advisor'].queryset = teachers_queryset
        self.fields['advisor'].label_from_instance = teacher_label
        
        self.fields['head_teacher'].queryset = teachers_queryset
        self.fields['head_teacher'].label_from_instance = teacher_label
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        start_class = cleaned_data.get('start_class_number')
        end_class = cleaned_data.get('end_class_number')
        
        if start_class and end_class:
            if start_class > end_class:
                raise ValidationError('Số lớp bắt đầu phải nhỏ hơn hoặc bằng số lớp kết thúc')
            
            if end_class - start_class > 10:
                raise ValidationError('Chỉ có thể tạo tối đa 10 lớp một lần')
        
        return cleaned_data 