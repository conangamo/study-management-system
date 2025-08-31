"""
Django forms for core app

NOTE: User account forms (StudentAccountForm, TeacherAccountForm, etc.) 
have been moved to core/forms/user_forms.py for better organization.
"""
from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from .models import (
    UserProfile, UserRole, Course, Assignment, Grade, Note, AssignmentSubmission, Document, DocumentCategory, DocumentComment, Class
)
from django.db.models import Q
import os


# USER ACCOUNT FORMS HAVE BEEN MOVED TO core/forms/user_forms.py
# The following forms are now in the new location:
# - StudentAccountForm
# - TeacherAccountForm  
# - BulkStudentAccountForm
# - BulkTeacherAccountForm
# - UserSearchForm


class CourseForm(forms.ModelForm):
    """Form quản lý môn học"""
    
    class Meta:
        model = Course
        fields = [
            'name', 'code', 'description', 'credits', 'semester', 
            'department', 'category', 'academic_year', 'start_date', 'end_date', 'max_students'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class GradeForm(forms.ModelForm):
    """Form quản lý điểm số"""
    
    class Meta:
        model = Grade
        fields = ['student', 'course', 'assignment', 'grade_type', 'score', 'max_score', 'comment', 'date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'assignment': forms.Select(attrs={'class': 'form-control'}),
            'grade_type': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class NoteForm(forms.ModelForm):
    """Form quản lý ghi chú"""
    
    class Meta:
        model = Note
        fields = ['title', 'content', 'is_pinned', 'course']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
        }


class UserCreationForm(forms.ModelForm):
    """Form tạo user mới"""
    
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Tạo UserProfile
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
        return user


class UserUpdateForm(forms.ModelForm):
    """Form cập nhật user"""
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 

# ==================== DOCUMENTS FORMS ====================

class DocumentUploadForm(forms.ModelForm):
    """Form upload tài liệu"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'course', 'category', 'file', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề tài liệu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả tài liệu (tùy chọn)'
            }),
            'course': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Lọc courses theo quyền của user
            if user.is_superuser:
                self.fields['course'].queryset = Course.objects.filter(status='active')
            else:
                # Kiểm tra UserProfile bằng cách khác
                try:
                    profile = UserProfile.objects.get(user=user)
                    if profile.role == 'teacher':
                        # Giáo viên chỉ thấy môn học họ phụ trách
                        self.fields['course'].queryset = Course.objects.filter(
                            Q(teacher=user) | Q(assistant_teachers=user),
                            status='active'
                        )
                    else:
                        # Sinh viên không thể upload
                        self.fields['course'].queryset = Course.objects.none()
                except UserProfile.DoesNotExist:
                    # Không có UserProfile
                    self.fields['course'].queryset = Course.objects.none()
        
        # Set queryset cho category
        self.fields['category'].queryset = DocumentCategory.objects.all()
        
        # Thêm empty_label cho các trường
        self.fields['course'].empty_label = "Chọn môn học"
        self.fields['category'].empty_label = "Chọn danh mục"
    
    def clean_file(self):
        """Validation cho file"""
        file = self.cleaned_data.get('file')
        if file:
            # Kiểm tra kích thước file (100MB)
            if file.size > 100 * 1024 * 1024:
                raise forms.ValidationError('Kích thước file không được vượt quá 100MB')
            
            # Kiểm tra loại file
            ext = os.path.splitext(file.name)[1].lower()
            allowed_extensions = ['.pdf', '.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx', 
                                '.txt', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3', '.zip', '.rar']
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'Loại file {ext} không được hỗ trợ')
        
        return file


class DocumentEditForm(forms.ModelForm):
    """Form chỉnh sửa tài liệu"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tiêu đề tài liệu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả tài liệu (tùy chọn)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class DocumentSearchForm(forms.Form):
    """Form tìm kiếm tài liệu"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm tài liệu...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.all(),
        required=False,
        empty_label="Tất cả danh mục",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(status='active'),
        required=False,
        empty_label="Tất cả môn học",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class DocumentCommentForm(forms.ModelForm):
    """Form bình luận tài liệu"""
    
    class Meta:
        model = DocumentComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Viết bình luận của bạn...'
            })
        }


class DocumentCategoryForm(forms.ModelForm):
    """Form quản lý danh mục tài liệu"""
    
    class Meta:
        model = DocumentCategory
        fields = ['name', 'description', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên danh mục'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả danh mục'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-file'
            })
        } 