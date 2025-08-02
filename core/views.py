from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

def home(request):
    """Trang chủ của ứng dụng"""
    return render(request, 'core/home.html')

@api_view(['GET'])
def course_list(request):
    """API endpoint cho danh sách khóa học"""
    return Response({'message': 'Course list API endpoint'})

@api_view(['GET'])
def assignment_list(request):
    """API endpoint cho danh sách bài tập"""
    return Response({'message': 'Assignment list API endpoint'})

@api_view(['GET'])
def grade_list(request):
    """API endpoint cho danh sách điểm số"""
    return Response({'message': 'Grade list API endpoint'})

@api_view(['GET'])
def note_list(request):
    """API endpoint cho danh sách ghi chú"""
    return Response({'message': 'Note list API endpoint'}) 