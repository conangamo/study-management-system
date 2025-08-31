"""
Document forms
Forms for document management
"""
from django import forms
from django.db.models import Q
import os

from ..models.documents import Document, DocumentCategory, DocumentComment
from ..models.study import Course
from ..models.user import UserProfile


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
    
    query = forms.CharField(
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