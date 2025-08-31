"""
Helper functions for the core app
"""

from django.utils import timezone
from datetime import datetime, timedelta


def get_letter_grade(percentage):
    """Chuyển đổi phần trăm sang điểm chữ"""
    if percentage >= 90:
        return 'A+'
    elif percentage >= 85:
        return 'A'
    elif percentage >= 80:
        return 'B+'
    elif percentage >= 75:
        return 'B'
    elif percentage >= 70:
        return 'C+'
    elif percentage >= 65:
        return 'C'
    elif percentage >= 60:
        return 'D+'
    elif percentage >= 55:
        return 'D'
    else:
        return 'F'


def calculate_gpa(grades):
    """Tính điểm trung bình có trọng số"""
    if not grades:
        return 0.0
    
    total_weighted_score = 0
    total_weight = 0
    
    for grade in grades:
        weight = grade.weight
        score = grade.score
        max_score = grade.max_score
        
        if max_score > 0:
            percentage = (score / max_score) * 100
            total_weighted_score += percentage * weight
            total_weight += weight
    
    if total_weight > 0:
        return total_weighted_score / total_weight
    return 0.0


def get_academic_year():
    """Lấy năm học hiện tại"""
    now = timezone.now()
    year = now.year
    
    # Nếu đang trong tháng 8-12, năm học là year-year+1
    # Nếu đang trong tháng 1-7, năm học là year-1-year
    if now.month >= 8:
        return f"{year}-{year + 1}"
    else:
        return f"{year - 1}-{year}"


def get_current_semester():
    """Lấy học kỳ hiện tại"""
    now = timezone.now()
    month = now.month
    
    if month in [9, 10, 11, 12, 1]:
        return '1'  # Học kỳ 1
    elif month in [2, 3, 4, 5]:
        return '2'  # Học kỳ 2
    elif month in [6, 7]:
        return '3'  # Học kỳ 3
    else:
        return 'summer'  # Học kỳ hè


def format_duration(duration):
    """Format thời gian duration"""
    if not duration:
        return "0 phút"
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours} giờ {minutes} phút"
    else:
        return f"{minutes} phút"


def is_weekend(date):
    """Kiểm tra có phải cuối tuần không"""
    return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday


def get_next_working_day(date):
    """Lấy ngày làm việc tiếp theo"""
    next_day = date + timedelta(days=1)
    while is_weekend(next_day):
        next_day += timedelta(days=1)
    return next_day


def truncate_text(text, max_length=100):
    """Cắt text nếu quá dài"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..." 