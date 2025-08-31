"""
User account forms for admin panel
"""
from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from ..models import UserProfile, Class


class StudentAccountForm(forms.ModelForm):
    """Form tạo tài khoản sinh viên"""
    
    # Thông tin cơ bản
    first_name = forms.CharField(
        max_length=30,
        label='Họ',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập họ'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label='Tên',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên'
        })
    )
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    
    student_id = forms.CharField(
        max_length=50,
        label='Mã sinh viên',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mã sinh viên'
        })
    )
    
    department = forms.ChoiceField(
        choices=UserProfile.DEPARTMENT_CHOICES,
        label='Khoa/Ngành',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    year_of_study = forms.IntegerField(
        min_value=2000,
        max_value=2030,
        label='Năm học',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2024'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Số điện thoại không hợp lệ'
            )
        ],
        label='Số điện thoại',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0123456789'
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
    
    # Tùy chọn mật khẩu
    password_option = forms.ChoiceField(
        choices=[
            ('auto', 'Tự động tạo mật khẩu'),
            ('custom', 'Nhập mật khẩu tùy chỉnh')
        ],
        initial='auto',
        label='Tùy chọn mật khẩu',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    custom_password = forms.CharField(
        max_length=128,
        required=False,
        min_length=8,
        label='Mật khẩu tùy chỉnh',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu tùy chỉnh (tối thiểu 8 ký tự)'
        })
    )
    
    # Tùy chọn email
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Gửi email chào mừng',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['department', 'year_of_study', 'phone']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 


class TeacherAccountForm(forms.ModelForm):
    """Form tạo tài khoản giảng viên"""
    
    # Thông tin cơ bản
    first_name = forms.CharField(
        max_length=30,
        label='Họ',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập họ'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label='Tên',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên'
        })
    )
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    
    department = forms.ChoiceField(
        choices=UserProfile.DEPARTMENT_CHOICES,
        label='Khoa/Ngành',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Số điện thoại không hợp lệ'
            )
        ],
        label='Số điện thoại',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0123456789'
        })
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        label='Giới thiệu',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Giới thiệu về giảng viên...'
        })
    )
    
    # Tùy chọn mật khẩu
    password_option = forms.ChoiceField(
        choices=[
            ('auto', 'Tự động tạo mật khẩu'),
            ('custom', 'Nhập mật khẩu tùy chỉnh')
        ],
        initial='auto',
        label='Tùy chọn mật khẩu',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    custom_password = forms.CharField(
        max_length=128,
        required=False,
        min_length=8,
        label='Mật khẩu tùy chỉnh',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu tùy chỉnh (tối thiểu 8 ký tự)'
        })
    )
    
    # Tùy chọn email
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Gửi email chào mừng',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['department', 'phone', 'bio']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 


class BulkStudentAccountForm(forms.Form):
    """Form tạo hàng loạt tài khoản sinh viên"""
    
    # File CSV
    csv_file = forms.FileField(
        label='File CSV',
        help_text='Upload file CSV với các cột: first_name,last_name,email,student_id,department,year_of_study,phone',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    
    # Tùy chọn mật khẩu
    password_option = forms.ChoiceField(
        choices=[
            ('auto', 'Tự động tạo mật khẩu (mật khẩu mặc định: Student@123)'),
            ('custom', 'Nhập mật khẩu tùy chỉnh')
        ],
        initial='auto',
        label='Tùy chọn mật khẩu',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    custom_password = forms.CharField(
        max_length=128,
        required=False,
        min_length=8,
        label='Mật khẩu tùy chỉnh',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu tùy chỉnh (tối thiểu 8 ký tự)'
        })
    )
    
    # Tùy chọn email
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Gửi email chào mừng cho tất cả',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Tùy chọn xử lý lỗi
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label='Bỏ qua lỗi và tiếp tục',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file:
            if not file.name.endswith('.csv'):
                raise forms.ValidationError('Chỉ chấp nhận file CSV')
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('File không được lớn hơn 5MB')
        return file
    
    def clean_custom_password(self):
        password_option = self.cleaned_data.get('password_option')
        custom_password = self.cleaned_data.get('custom_password')
        
        if password_option == 'custom' and not custom_password:
            raise forms.ValidationError('Vui lòng nhập mật khẩu tùy chỉnh')
        
        if custom_password and len(custom_password) < 8:
            raise forms.ValidationError('Mật khẩu phải có ít nhất 8 ký tự')
        
        return custom_password


class BulkTeacherAccountForm(forms.Form):
    """Form tạo hàng loạt tài khoản giảng viên"""
    
    # File CSV
    csv_file = forms.FileField(
        label='File CSV',
        help_text='Upload file CSV với các cột: first_name,last_name,email,department,phone,bio',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    
    # Tùy chọn mật khẩu
    password_option = forms.ChoiceField(
        choices=[
            ('auto', 'Tự động tạo mật khẩu (mật khẩu mặc định: Teacher@123)'),
            ('custom', 'Nhập mật khẩu tùy chỉnh')
        ],
        initial='auto',
        label='Tùy chọn mật khẩu',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    custom_password = forms.CharField(
        max_length=128,
        required=False,
        min_length=8,
        label='Mật khẩu tùy chỉnh',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu tùy chỉnh (tối thiểu 8 ký tự)'
        })
    )
    
    # Tùy chọn email
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Gửi email chào mừng cho tất cả',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Tùy chọn xử lý lỗi
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label='Bỏ qua lỗi và tiếp tục',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file:
            if not file.name.endswith('.csv'):
                raise forms.ValidationError('Chỉ chấp nhận file CSV')
            if file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('File không được lớn hơn 5MB')
        return file
    
    def clean_custom_password(self):
        password_option = self.cleaned_data.get('password_option')
        custom_password = self.cleaned_data.get('custom_password')
        
        if password_option == 'custom' and not custom_password:
            raise forms.ValidationError('Vui lòng nhập mật khẩu tùy chỉnh')
        
        if custom_password and len(custom_password) < 8:
            raise forms.ValidationError('Mật khẩu phải có ít nhất 8 ký tự')
        
        return custom_password


class UserSearchForm(forms.Form):
    """Form tìm kiếm người dùng"""
    
    search_query = forms.CharField(
        max_length=100,
        required=False,
        label='Tìm kiếm',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm theo tên, email, MSSV...'
        })
    )
    
    role_filter = forms.ChoiceField(
        choices=[('', 'Tất cả vai trò')] + UserProfile.ROLE_CHOICES,
        required=False,
        label='Vai trò',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    department_filter = forms.ChoiceField(
        choices=[('', 'Tất cả khoa')] + UserProfile.DEPARTMENT_CHOICES,
        required=False,
        label='Khoa/Ngành',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    status_filter = forms.ChoiceField(
        choices=[
            ('', 'Tất cả trạng thái'),
            ('active', 'Đang hoạt động'),
            ('inactive', 'Đã khóa'),
            ('verified', 'Đã xác thực'),
            ('unverified', 'Chưa xác thực')
        ],
        required=False,
        label='Trạng thái',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        label='Từ ngày',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Đến ngày',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Ngày bắt đầu phải trước ngày kết thúc')
        
        return cleaned_data 